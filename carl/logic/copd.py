"""COPD module"""
from flask import current_app

from carl.modules.coding import Coding
from carl.modules.codeableconcept import CodeableConcept
from carl.modules.condition import Condition, mark_patient_with_condition
from carl.modules.patient import Patient, patient_has
from carl.modules.resource import delete_resource
from carl.modules.valueset import valueset_codings

# ValueSet for all known COPD Condition codings - should match "url" in:
# ``carl.serialized.COPD_valueset.json``

COPD_VALUESET_URI = "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-codings"

# ValueSet for all known COPD MedicationRequest codings - should match "url" in:
# ``carl.serialized.COPD_medication_valueset.json``
COPD_MEDICATION_VALUESET_URI = (
    "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-medication-codings"
)


# Designated coding used to tag users eligible for COPD questionnaire
CNICS_COPD_coding = Coding(
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.COPD2021.11.001",
    display="COPD PRO group member",
)

# Designated coding used to tag COPD PRO group members with qualifying MedicationRequest
CNICS_COPD_medication_coding = Coding(
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.COPDMED2022.03.001",
    display="COPD PRO group member with qualifying MedicationRequest",
)


def process_4_COPD_conditions(patient_id):
    """Process given patient for COPD conditions

    NB: generates side effects, namely a special Condition is persisted in the
    configured FHIR store for patients found to have a qualifying COPD Condition
    """
    current_app.logger.debug(f"process {patient_id} for COPD Conditions")

    # process for matching conditions in value set
    condition_codings = valueset_codings(COPD_VALUESET_URI)
    positive_codings = patient_has(
        patient_id=patient_id,
        resource_type="Condition",
        resource_codings=condition_codings,
    )
    results = {
        "patient_id": patient_id,
        "COPD Condition codings found": len(positive_codings) > 0,
    }
    if not positive_codings:
        return results

    return mark_patient_with_condition(patient_id, CNICS_COPD_coding, results)


def process_4_COPD_medications(patient_id):
    """Process given patient for COPD medications

    NB: generates side effects, namely a special Condition is persisted in the
    configured FHIR store for patients found to have a qualifying COPD MedicationRequest
    """
    current_app.logger.debug(f"process {patient_id} for COPD Medications")

    # process for mediation requests in value set
    medication_codings = valueset_codings(COPD_MEDICATION_VALUESET_URI)
    positive_codings = patient_has(
        patient_id=patient_id,
        resource_type="MedicationRequest",
        resource_codings=medication_codings,
        code_attribute="medicationCodeableConcept",
    )
    results = {
        "patient_id": patient_id,
        "COPD MedicationRequest codings found": len(positive_codings) > 0,
    }
    if not positive_codings:
        return results

    return mark_patient_with_condition(
        patient_id, CNICS_COPD_medication_coding, results
    )


def classify_for_COPD(patient_id):
    """classify given patient for diabetes

    NB: generates side effects, namely a special Conditions are persisted in the
    configured FHIR store for patients found to have a COPD using
    the following criteria (applied in order, looking only till any case evaluates false):
    - If patient has at least one Condition from the CNICS COPD codings value set,
    mark patient with the CNICS_COPD_coding Condition
    - If patient has at least one MedicationRequest from the CNICS COPD medication coding
    value set, mark patient with the CNICS_COPD_medication_coding Condition
    """
    results = process_4_COPD_conditions(patient_id)
    # We only consider COPD meds if the patient obtained the COPD condition
    # success is recorded in a key with the <condition.code>_matched pattern
    if any(key.endswith("matched") for key in results.keys()):
        results.update(process_4_COPD_medications(patient_id))
    return results


def remove_COPD_classification(patient_id):
    """declassify given patient, i.e. remove added COPD Conditions

    Function used to reset or declassify patients previously found to have COPD,
    this will remove the special Condition added during the classification step,
    if found from the given patient.

    NB: generates side effects, namely special Conditions are removed from the
    configured FHIR store for patients found to have previously gained said Conditions
    """
    current_app.logger.debug(f"declassify {patient_id} of COPD")
    classified_COPD_codings = set([CNICS_COPD_coding, CNICS_COPD_medication_coding])
    previously_classified = patient_has(
        patient_id=patient_id,
        resource_codings=classified_COPD_codings,
        resource_type="Condition",
    )
    results = {
        "patient_id": patient_id,
        "COPD classification found": len(previously_classified) > 0,
    }
    if not previously_classified:
        return results

    # Blindly try to remove all, knowing only one may be present on a patient
    for coding in classified_COPD_codings:
        condition = Condition()
        condition.code = CodeableConcept(coding)
        condition.subject = Patient(patient_id)
        delete_resource(resource=condition)

    results["COPD_matched"] = True

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
