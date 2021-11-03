"""FHIR Coding module"""
from carl.modules.resource import Resource


class Coding(Resource):
    """FHIR Coding - used for serializing and queries"""

    def __init__(self, code, system):
        super().__init__()
        self._fields['code'] = code
        self._fields['system'] = system

    @staticmethod
    def unique_params():
        return tuple(['code', 'system'])

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        return cls(code=data['code'], system=data['system'])
