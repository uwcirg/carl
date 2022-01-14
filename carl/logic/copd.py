"""COPD module"""
from flask import current_app, has_app_context
import requests

from carl.config import FHIR_SERVER_URL
from carl.modules.coding import Coding
from carl.modules.codeableconcept import CodeableConcept
from carl.modules.condition import Condition
from carl.modules.paging import next_resource_bundle
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

CNICS_IDENTIFIER_SYSTEM = "https://cnics.cirg.washington.edu/site-patient-id/"


def patient_canonical_identifier(patient_id, site_code):
    """Return system|value identifier if patient has one for preferred system"""
    url = f"{FHIR_SERVER_URL}Patient/{patient_id}"
    response = requests.get(url)
    if has_app_context():
        current_app.logger.debug(f"HAPI GET: {response.url}")
    response.raise_for_status()

    match = [
        f"{identifier['system']}|{identifier['value']}"
        for identifier in response.json().get("identifier", [])
        if identifier['system'] == CNICS_IDENTIFIER_SYSTEM + site_code]

    if match:
        return match[0]


def patient_has(patient_id, condition_codings):
    """Determine if given patient has at least one condition in given codings

    :returns: intersection of patient's condition codings and those given
    """
    patient_codings = set()
    for bundle in next_resource_bundle(
            resource_type='Condition',
            search_params={'subject': patient_id}):
        for entry in bundle.get('entry', []):
            for coding in entry['resource']['code']['coding']:
                patient_codings.add(Coding(system=coding['system'], code=coding['code']))

    return patient_codings.intersection(condition_codings)


def delete_resource(resource):
    """Delete given resource from FHIR_SERVER_URL

    NB - this doesn't round-trip check if given resource already exists,
    but rather does a DELETE with necessary search params to prevent duplicate
    writes.  AKA conditional delete: https://www.hl7.org/fhir/http.html#cond-delete
    """
    url = f"{FHIR_SERVER_URL}{resource.search_url()}"
    response = requests.delete(url=url, json=resource.as_fhir())
    current_app.logger.debug(f"HAPI DELETE: {response.url}")
    response.raise_for_status()
    return response.json()


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


def process_4_COPD(patient_id, site_code):
    """Process given patient for COPD

    NB: generates side-effects, namely a special Condition is persisted in the
    configured FHIR store for patients found to have a qualifying COPD Condition
    """
    current_app.logger.debug(f"process {patient_id} for COPD")
    condition_codings = valueset_codings(COPD_VALUESET_URI)
    positive_codings = patient_has(
        patient_id=patient_id, condition_codings=condition_codings)
    results = {
        "patient_id": patient_canonical_identifier(patient_id, site_code) or patient_id,
        "COPD codings found": len(positive_codings) > 0}
    if not positive_codings:
        return results

    condition = Condition()
    condition.code = CodeableConcept(CNICS_COPD_coding)
    condition.subject = Patient(patient_id)
    response = persist_resource(resource=condition)
    results['matched'] = True
    results['condition'] = response
    results['intersection'] = [coding.as_fhir() for coding in positive_codings]

    current_app.logger.debug(results)
    return results


def remove_COPD_classification(patient_id, site_code):
    """declassify given patient, i.e. remove added COPD Condition

    Function used to reset or declassify patients previously found to have COPD,
    this will remove the special Condition added during the classification step,
    if found from the given patient.

    NB: generates side-effects, namely a special Condition is removed from the
    configured FHIR store for patients found to have previously gained said Condition
    """
    current_app.logger.debug(f"declassify {patient_id} of COPD")
    classified_COPD_coding = set([CNICS_COPD_coding])
    previously_classified = patient_has(
        patient_id=patient_id, condition_codings=classified_COPD_coding)
    results = {
        "patient_id": patient_canonical_identifier(patient_id, site_code) or patient_id,
        "COPD classification found": len(previously_classified) > 0}
    if not previously_classified:
        return results

    condition = Condition()
    condition.code = CodeableConcept(CNICS_COPD_coding)
    condition.subject = Patient(patient_id)
    delete_resource(resource=condition)
    results['matched'] = True

    current_app.logger.debug(results)
    return results
