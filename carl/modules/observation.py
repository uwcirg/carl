"""FHIR Observation module"""
from carl.modules.paging import next_resource_bundle
from carl.modules.reference import Reference
from carl.modules.resource import Resource
from carl.modules.valuequantity import ValueQuantity


class Observation(Resource):
    """FHIR Observation - used for (de)serializing and queries"""

    RESOURCE_TYPE = "Observation"

    def __init__(self):
        """Minimum necessary to uniquely define or query"""
        super().__init__()

    @property
    def code(self):
        return self._fields.get("code")

    @code.setter
    def code(self, codeable_concept):
        self._fields["code"] = codeable_concept

    @property
    def valuequantity(self):
        return self._fields.get("valueQuantity")

    @valuequantity.setter
    def value_quantity(self, valuequantity):
        self._fields["valueQuantity"] = valuequantity

    def value_quantity_above_threshold(self, threshold):
        assert self.valuequantity
        return self.valuequantity['value'] > float(threshold)

    @property
    def subject(self):
        return self._fields.get("subject")

    @subject.setter
    def subject(self, resource):
        self._fields["subject"] = Reference(resource)

    @staticmethod
    def unique_params():
        return tuple(["code", "subject"])


def patient_observations(patient_id, resource_coding):
    """Return list of Observations for given patient, with given coding
    """
    patient_obs = list()
    for bundle in next_resource_bundle(
            resource_type=Observation,
            search_params={
                "subject": patient_id,
                "code": f"{resource_coding.system}|{resource_coding.code}"
            }):
        for entry in bundle.get("entry", []):
            obs = Observation()
            try:
                codings = entry["resource"][code_attribute]["coding"]
            except KeyError as deets:
                raise ValueError(f"failed lookup in {entry}: {deets}")
            for coding in codings:
                patient_codings.add(
                    Coding(system=coding["system"], code=coding["code"])
                )

    return patient_codings.intersection(resource_codings)

