"""FHIR Coding module"""
from carl.modules.resource import Resource


class Coding(Resource):
    """FHIR Coding - used for serializing and queries"""
    RESOURCE_TYPE = 'Coding'

    def __init__(self, code, system, display=None):
        super().__init__()
        self._fields['code'] = code
        self._fields['system'] = system
        if display:
            self._fields['display'] = display

    @property
    def code(self):
        return self._fields.get('code')

    @property
    def system(self):
        return self._fields.get('system')

    @staticmethod
    def unique_params():
        return tuple(['code', 'system'])

    def value_param(self):
        """Akin to `search_url`, but to only return the value portion

        Codings are often nested attributes, use in a search filter as
        [parameter]=[system]|[code] - this method returns on the right
        side or `value` portion of that query string.

        See also https://www.hl7.org/fhir/search.html#token
        """
        return '|'.join((self.system, self.code))

    def as_fhir(self):
        return dict(self._fields)

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        return cls(code=data['code'], system=data['system'], display=data.get('display'))

    def __eq__(self, other):
        """Logical equals operator - needed for set functionality"""
        return (
            self._fields.get('code') == other._fields.get('code') and
            self._fields.get('system') == other._fields.get('system'))

    def __hash__(self):
        """Generate logically unique hash for set functionality"""
        return hash(f"{self._fields.get('system')}|{self._fields.get('code')}")
