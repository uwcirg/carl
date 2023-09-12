from collections import OrderedDict
import logging
import requests
from urllib.parse import urlencode

from carl.config import FHIR_SERVER_URL


class Resource(object):
    """Abstract Base class for FHIR resources"""

    def __init__(self):
        self._fields = OrderedDict()
        self._id = None

    def __repr__(self):
        if self._id is not None:
            return f"<{self.RESOURCE_TYPE}/{self._id}>"
        else:
            return f"<{self.RESOURCE_TYPE}>"

    def id(self):
        """Look up FHIR id or return None if not found"""
        if self._id is not None:
            return self._id

        # Round-trip to see if this represents a new or existing resource
        if FHIR_SERVER_URL:
            headers = {"Cache-Control": "no-cache"}
            response = requests.get(
                "/".join((FHIR_SERVER_URL, self.search_url())),
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            # extract Resource.id from bundle
            bundle = response.json()
            if bundle["total"]:
                if bundle["total"] > 1:
                    raise RuntimeError(
                        "Found multiple matches, can't generate upsert"
                        f"for {self.search_url()}"
                    )
                assert (
                    bundle["entry"][0]["resource"]["resourceType"] == self.RESOURCE_TYPE
                )
                self._id = bundle["entry"][0]["resource"]["id"]
        return self._id

    def as_fhir(self):
        results = {"resourceType": self.RESOURCE_TYPE}
        for field in self._fields:
            if hasattr(self._fields[field], "as_fhir"):
                results[field] = self._fields[field].as_fhir()
            else:
                results[field] = self._fields[field]
        return results

    def search_url(self):
        """Generate the request path search url for resource

        NB - this method does NOT invoke a round trip ID lookup.
        Call self.id() beforehand to force a lookup.
        """
        if self._id:
            return f"{self.RESOURCE_TYPE}/{self._id}"

        search_params = dict()
        for field in self.unique_params():
            # See if resource provides direct (overloaded) field access
            attr = getattr(self, field, None)
            if not attr:
                # Otherwise, check in _fields
                attr = self._fields.get(field, None)
            if not attr:
                # Not defined, skip
                continue

            # Some attributes include a `value_param()` method should
            # specialization be needed when used in search params
            if hasattr(attr, "value_param"):
                value = getattr(attr, "value_param")()
            else:
                value = attr
            search_params[field] = value

        return f"{self.RESOURCE_TYPE}?{urlencode(search_params)}"


def delete_resource(resource):
    """Delete given resource from FHIR_SERVER_URL

    NB - this doesn't round-trip check if given resource already exists,
    but rather does a DELETE with necessary search params to prevent duplicate
    writes.  AKA conditional delete: https://www.hl7.org/fhir/http.html#cond-delete
    """
    url = f"{FHIR_SERVER_URL}{resource.search_url()}"
    response = requests.delete(url=url, json=resource.as_fhir(), timeout=30)
    logging.debug(f"HAPI DELETE: {response.url}")
    response.raise_for_status()
    return response.json()


def persist_resource(resource):
    """Persist given resource to FHIR_SERVER_URL

    NB - this doesn't round-trip check if given resource already exists,
    but rather does a PUT with necessary search params to prevent duplicate
    writes.  AKA conditional update: https://www.hl7.org/fhir/http.html#cond-update
    """
    url = f"{FHIR_SERVER_URL}{resource.search_url()}"
    response = requests.put(url=url, json=resource.as_fhir(), timeout=30)
    logging.debug(f"HAPI PUT: {response.url}")
    response.raise_for_status()
    return response.json()
