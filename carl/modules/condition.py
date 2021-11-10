"""FHIR Condition module"""
from carl.modules.reference import Reference
from carl.modules.resource import Resource


class Condition(Resource):
    """FHIR Condition - used for (de)serializing and queries"""
    RESOURCE_TYPE = 'Condition'

    def __init__(self):
        """Minimum necessary to uniquely define or query"""
        super().__init__()

    @property
    def code(self):
        return self._fields.get('code')

    @code.setter
    def code(self, codeable_concept):
        self._fields['code'] = codeable_concept

    @property
    def subject(self):
        return self._fields.get('subject')

    @subject.setter
    def subject(self, resource):
        self._fields['subject'] = Reference(resource)

    @staticmethod
    def unique_params():
        return tuple(['code', 'subject'])
