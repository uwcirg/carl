"""FHIR ValueSet module"""
import requests

from carl.config import FHIR_SERVER_URL
from carl.modules.coding import Coding
from carl.modules.resource import Resource


class ValueSet(Resource):
    """FHIR ValueSet - used for (de)serializing and queries"""

    RESOURCE_TYPE = "ValueSet"

    def __init__(self, url):
        """Minimum necessary to uniquely define or query"""
        super().__init__()
        self._fields["url"] = url

    @staticmethod
    def unique_params():
        return tuple(["url"])

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        return cls(url=data["url"])


# TODO: cache this never changing round-trip
def valueset_codings(url):
    """Obtain set of codings in matching ValueSet by url field"""
    search_params = {"url": url}
    resource_path = f"{FHIR_SERVER_URL}ValueSet"
    response = requests.get(resource_path, params=search_params, timeout=30)
    response.raise_for_status()
    bundle = response.json()
    if bundle["total"] != 1:
        raise ValueError(
            f"Expected ValueSet {url} not found; Did `flask bootstrap` get called?"
        )

    value_set = bundle["entry"][0]["resource"]
    codings = set()
    for entry in value_set.get("compose").get("include"):
        # By system, then nested codes - parse and add.
        system = entry["system"]
        for concept in entry.get("concept"):
            codings.add(Coding(system=system, code=concept["code"]))

    return codings
