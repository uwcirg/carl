"""FHIR Observation module"""
from carl.modules.codeableconcept import CodeableConcept
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
    def valuequantity(self, valuequantity):
        self._fields["valueQuantity"] = valuequantity

    def valuequantity_above_threshold(self, threshold):
        if not self.valuequantity:
            return None
        return self.valuequantity['value'] > float(threshold)

    @property
    def subject(self):
        return self._fields.get("subject")

    @subject.setter
    def subject(self, resource):
        if isinstance(resource, Reference):
            self._fields["subject"] = resource
        else:
            self._fields["subject"] = Reference(resource)

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        instance = cls()
        instance.code = CodeableConcept.from_fhir(data["code"])
        instance.subject = Reference.from_fhir(data["subject"])
        instance.valuequantity = ValueQuantity.from_fhir(data["valueQuantity"])
        return instance

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
            obs = Observation.from_fhir(entry["resource"])
            patient_obs.append(obs)

    return patient_obs

