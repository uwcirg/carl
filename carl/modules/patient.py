"""FHIR ValueSet module"""
from carl.modules.coding import Coding
from carl.modules.paging import next_resource_bundle
from carl.modules.resource import Resource


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
                raise ValueError(f"failed lookup in {entry}: {deets}")
            for coding in codings:
                patient_codings.add(
                    Coding(system=coding["system"], code=coding["code"])
                )

    return patient_codings.intersection(resource_codings)
