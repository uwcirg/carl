"""FHIR ValueSet module"""
import requests

from carl.config import FHIR_SERVER_URL
from carl.modules.coding import Coding
from carl.modules.resource import Resource


class Patient(Resource):
    """FHIR Patient - used for (de)serializing and queries"""
    RESOURCE_TYPE = 'Patient'

    def __init__(self, id=None):
        super().__init__()
        self._id = id

    def value_param(self):
        """Akin to `search_url`, but to only return the value portion

        Patients are often nested as "refernce" attributes.  When used
        in the value position of a query string, just the patient id is used.

        See also https://www.hl7.org/fhir/search.html#token
        """
        return self.id()
