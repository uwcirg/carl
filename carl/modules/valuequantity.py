"""FHIR ValueQuantity module"""
from flask import current_app

from carl.modules.codeableconcept import CodeableConcept
from carl.modules.patient import Patient
from carl.modules.reference import Reference
from carl.modules.resource import Resource, persist_resource


class ValueQuantity(Resource):
    """FHIR ValueQuantity - used for (de)serializing and queries"""

    RESOURCE_TYPE = "ValueQuantity"

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
    def system(self):
        return self._fields.get("system")

    @system.setter
    def system(self, system):
        self._fields["system"] = system

    @property
    def unit(self):
        return self._fields.get("unit")

    @unit.setter
    def unit(self, unit):
        self._fields["unit"] = unit

    @property
    def value(self):
        return self._fields.get("value")

    @value.setter
    def value(self, value):
        self._fields["value"] = value

    @staticmethod
    def unique_params():
        return tuple(["value", "unit", "system"])

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        instance = cls()
        instance.code = data["code"]
        instance.value = data["value"]
        instance.unit = data["unit"]
        instance.system = data["system"]
        return instance
