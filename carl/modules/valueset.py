"""FHIR ValueSet module"""
from carl.modules.resource import Resource


class ValueSet(Resource):
    """FHIR ValueSet - used for (de)serializing and queries"""
    RESOURCE_TYPE = 'ValueSet'

    def __init__(self, url):
        """Minimum necessary to uniquely define or query"""
        super().__init__()
        self._fields['url'] = url

    @staticmethod
    def unique_params():
        return tuple(['url'])

    @classmethod
    def from_fhir(cls, data):
        """Deserialize from json (FHIR) data"""
        return cls(url=data['url'])
