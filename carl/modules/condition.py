"""FHIR Condition module"""
from flask import current_app

from carl.modules.codeableconcept import CodeableConcept
from carl.modules.patient import Patient
from carl.modules.reference import Reference
from carl.modules.resource import Resource, persist_resource


class Condition(Resource):
    """FHIR Condition - used for (de)serializing and queries"""

    RESOURCE_TYPE = "Condition"

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
    def subject(self):
        return self._fields.get("subject")

    @subject.setter
    def subject(self, resource):
        self._fields["subject"] = Reference(resource)

    @staticmethod
    def unique_params():
        return tuple(["code", "subject"])


def mark_patient_with_condition(patient_id, condition_coding, results):
    condition = Condition()
    condition.code = CodeableConcept(condition_coding)
    condition.subject = Patient(patient_id)
    response = persist_resource(resource=condition)
    results["matched"] = True
    results["condition"] = response
    # results["intersection"] = [coding.as_fhir() for coding in positive_codings]

    current_app.logger.debug(results)
    return results
