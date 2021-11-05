"""FHIR Coding module"""
from carl.modules.resource import Resource


class Coding(Resource):
    """FHIR Coding - used for serializing and queries"""
    RESOURCE_TYPE = 'Coding'

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

    def __eq__(self, other):
        """Logical equals operator - needed for set functionality"""
        return (
            self._fields.get('code') == other._fields.get('code') and
            self._fields.get('system') == other._fields.get('system'))

    def __hash__(self):
        """Generate logically unique hash for set functionality"""
        return hash(f"{self._fields.get('system')}|{self._fields.get('code')}")
