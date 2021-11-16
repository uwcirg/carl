"""COPD module"""
from flask import current_app
import requests

from carl.config import FHIR_SERVER_URL
from carl.modules.coding import Coding
from carl.modules.codeableconcept import CodeableConcept
from carl.modules.condition import Condition
from carl.modules.patient import Patient
from carl.modules.valueset import valueset_codings

# ValueSet for all known COPD condition codings - should match "url" in:
# ``carl.serialized.COPD_valueset.json``
COPD_VALUESET_URI = "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-codings"

# Designated coding used to tag users eligible for COPD questionnaire
CNICS_COPD_coding = Coding(
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.COPD2021.11.001",
    display="COPD PRO group member")


def patient_has(patient_id, value_set_uri):
    """Determine if given patient has condition defined by given ValueSet

    :returns: intersection of patient's condition codings and those in given ValueSet
    """
    search_params = {'patient': patient_id}
    url = f"{FHIR_SERVER_URL}Condition"
    response = requests.get(url, params=search_params)
    current_app.logger.debug(f"HAPI GET: {response.url}")
    response.raise_for_status()

    patient_codings = set()
    bundle = response.json()
    for entry in bundle.get('entry', []):
        for coding in entry['resource']['code']['coding']:
            patient_codings.add(Coding(system=coding['system'], code=coding['code']))

    condition_codings = valueset_codings(value_set_uri)
    return patient_codings.intersection(condition_codings)


def persist_resource(resource):
    """Persist given resource to FHIR_SERVER_URL

    NB - this doesn't round-trip check if given resource already exists,
    but rather does a PUT with necessary search params to prevent duplicate
    writes.  AKA conditional update: https://www.hl7.org/fhir/http.html#cond-update
    """
    url = f"{FHIR_SERVER_URL}{resource.search_url()}"
    response = requests.put(url=url, json=resource.as_fhir())
    current_app.logger.debug(f"HAPI PUT: {response.url}")
    response.raise_for_status()
    return response.json()


def process_4_COPD(patient_id):
    """Process given patient for COPD

    NB: generates side-effects, namely a special Condition is persisted in the
    configured FHIR store for patients found to have a qualifying COPD Condition
    """
    current_app.logger.debug(f"process {patient_id} for COPD")
    positive_codings = patient_has(patient_id=patient_id, value_set_uri=COPD_VALUESET_URI)
    results = {
        "patient_id": patient_id,
        "COPD codings found": len(positive_codings) > 0}
    if not positive_codings:
        return results

    condition = Condition()
    condition.code = CodeableConcept(CNICS_COPD_coding)
    condition.subject = Patient(patient_id)
    response = persist_resource(resource=condition)
    results['condition'] = response

    return results