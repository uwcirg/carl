"""FHIR ValueSet module"""
import requests
from flask import has_app_context, current_app

from carl.config import FHIR_SERVER_URL
from carl.modules.coding import Coding
from carl.modules.paging import next_resource_bundle
from carl.modules.resource import Resource

CNICS_IDENTIFIER_SYSTEM = "https://cnics.cirg.washington.edu/site-patient-id/"


class Patient(Resource):
    """FHIR Patient - used for (de)serializing and queries"""

    RESOURCE_TYPE = "Patient"

    def __init__(self, id=None):
        super().__init__()
        self._id = id

    def value_param(self):
        """Akin to `search_url`, but to only return the value portion

        Patients are often nested as "reference" attributes.  When used
        in the value position of a query string, just the patient id is used.

        See also https://www.hl7.org/fhir/search.html#token
        """
        return self.id()


def patient_has(patient_id, resource_type, resource_codings, code_attribute="code"):
    """Determine if given patient has at least one matching resource in given codings

    :returns: intersection of patient's resource with the given codings
    """
    patient_codings = set()
    for bundle in next_resource_bundle(
        resource_type=resource_type, search_params={"subject": patient_id}
    ):
        for entry in bundle.get("entry", []):
            try:
                codings = entry["resource"][code_attribute]["coding"]
            except KeyError as deets:
                raise ValueError(f"failed lookup, '{deets}' not in {entry}")
            for coding in codings:
                patient_codings.add(
                    Coding(system=coding["system"], code=coding["code"])
                )

    return patient_codings.intersection(resource_codings)


def patient_canonical_identifier(patient_id, site_code):
    """Return system|value identifier if patient has one for preferred system"""
    url = f"{FHIR_SERVER_URL}Patient/{patient_id}"
    response = requests.get(url, timeout=30)
    if has_app_context():
        current_app.logger.debug(f"HAPI GET: {response.url}")
    response.raise_for_status()

    match = [
        f"{identifier['system']}|{identifier['value']}"
        for identifier in response.json().get("identifier", [])
        if identifier["system"] == CNICS_IDENTIFIER_SYSTEM + site_code
    ]

    if match:
        return match[0]
