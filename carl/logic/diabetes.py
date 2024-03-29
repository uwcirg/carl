"""diabetes module"""
from flask import current_app

from carl.modules.coding import Coding
from carl.modules.codeableconcept import CodeableConcept
from carl.modules.condition import Condition, mark_patient_with_condition
from carl.modules.observation import patient_observations
from carl.modules.patient import Patient, patient_has
from carl.modules.resource import delete_resource
from carl.modules.valueset import valueset_codings

# ValueSets for all known diabetes MedicationRequest codings - should match "url"s in:
# ``carl.serialized.diabetes_related_medication_valueset.json``
# ``carl.serialized.diabetes_specific_medication_valueset.json``
vs_base = "http://cnics-cirg.washington.edu/fhir/ValueSet/"
DIABETES_RELATED_MEDICATION_VALUESET_URI = (
    f"{vs_base}CNICS-diabetes-related-medication-codings"
)
DIABETES_SPECIFIC_MEDICATION_VALUESET_URI = (
    f"{vs_base}CNICS-diabetes-specific-medication-codings"
)

# ValueSet for all known diabetes Condition codings - should match "url" in:
# ``carl.serialized.diabetes_conditions_valueset.json``
DIABETES_CONDITIONS_VALUESET_URL = f"{vs_base}CNICS-Diabetes-Conditions"

# ValueSet for all known diabetes Diagnosis codings - should match "url" in:
# ``carl.serialized.diabetes_diagnosis_valueset.json``
DIABETES_DX_VALUESET_URI = f"{vs_base}CNICS-diabetes-diagnosis-codings"

# Observation (lab) code of interest
A1C_observation_coding = Coding(
    system="https://cnics.cirg.washington.edu/test-name",
    code="Hemoglobin A1C",
    display="Hemoglobin A1C",
)

# Designated Condition.coding assigned if patient found to meet the diabetes criteria
CNICS_diabetes_coding = Coding(
    system="https://cpro.cirg.washington.edu/groups",
    code="CNICS.diabetes2023.07.001",
    display="COPD diabetes criteria group member",
)


def process_labs(patient_id):
    threshold = 6.5
    labs = patient_observations(
        patient_id=patient_id, resource_coding=A1C_observation_coding
    )
    results = {
        "patient_id": patient_id,
        f"{A1C_observation_coding.code} count": len(labs),
    }
    for obs in labs:
        if obs.value_above_threshold(threshold):
            results["Hemoglobin-A1C-threshold_matched"] = True
            break
    return results


def process_diagnoses(patient_id):
    # process for conditions in value set
    conditions = valueset_codings(DIABETES_CONDITIONS_VALUESET_URL)
    positive_codings = patient_has(
        patient_id=patient_id,
        resource_type="Condition",
        resource_codings=conditions,
        code_attribute="code",
    )
    results = {
        "patient_id": patient_id,
        "Diabetes Condition codings found": len(positive_codings) > 0,
    }
    if not positive_codings:
        return results
    results["Diabetes-Conditions_matched"] = True
    return results


def has_medications(patient_id, medication_value_set):
    med_codings = valueset_codings(medication_value_set)
    positive_codings = patient_has(
        patient_id=patient_id,
        resource_type="MedicationRequest",
        resource_codings=med_codings,
        code_attribute="medicationCodeableConcept",
    )
    results = dict()
    results[f"{medication_value_set.split('/')[-1]} count"] = len(positive_codings)
    if len(positive_codings) > 0:
        results[f"{medication_value_set.split('/')[-1]}_matched"] = True
    return results


def classify_for_diabetes(patient_id):
    """classify given patient for diabetes

    NB: generates side effects, namely a special Condition is persisted in the
    configured FHIR store for patients found to have a diabetes using
    the following criteria (applied in order, looking only till any case evaluates true):
    - 1) Observation Hemoglobin A1C with valueQuantity >= 6.5
    - 2) MedicationRequest for any diabetes-specific medication
    - 3) MedicationRequest for any diabetes-related medication AND Diagnosis for diabetes
    """

    def tag_with_condition(results):
        return mark_patient_with_condition(patient_id, CNICS_diabetes_coding, results)

    current_app.logger.debug(f"process {patient_id} for diabetes Condition")

    # Criteria #1
    results = process_labs(patient_id)
    if any(key.endswith("matched") for key in results.keys()):
        return tag_with_condition(results)

    # Criteria #2
    results.update(
        has_medications(patient_id, DIABETES_SPECIFIC_MEDICATION_VALUESET_URI)
    )
    if any(key.endswith("matched") for key in results.keys()):
        return tag_with_condition(results)

    # Criteria #3-a
    related_results = has_medications(
        patient_id, DIABETES_RELATED_MEDICATION_VALUESET_URI
    )
    if not any(key.endswith("matched") for key in related_results.keys()):
        results.update(related_results)
        return results

    # Criteria #3-b
    diagnoses_results = process_diagnoses(patient_id)
    if not any(key.endswith("matched") for key in diagnoses_results.keys()):
        results.update(related_results)
        results.update(diagnoses_results)
        return results

    # still here implies related_medications and process_diagnosis both returned true,
    # i.e. Criteria 3 is true
    results.update(related_results)
    results.update(diagnoses_results)
    return tag_with_condition(results)


def remove_diabetes_classification(patient_id):
    """declassify given patient, i.e. remove added diabetes Conditions

    Function used to reset or declassify patients previously found to have diabetes,
    this will remove the special Condition added during the classification step,
    if found from the given patient.

    NB: generates side effects, namely special Conditions are removed from the
    configured FHIR store for patients found to have previously gained said Conditions
    """
    current_app.logger.debug(f"declassify {patient_id} of diabetes")
    classified_diabetes_codings = set([CNICS_diabetes_coding])
    previously_classified = patient_has(
        patient_id=patient_id,
        resource_codings=classified_diabetes_codings,
        resource_type="Condition",
    )
    results = {
        "patient_id": patient_id,
        "diabetes classification found": len(previously_classified) > 0,
    }
    if not previously_classified:
        return results

    # Blindly try to remove all, knowing only one may be present on a patient
    for coding in classified_diabetes_codings:
        condition = Condition()
        condition.code = CodeableConcept(coding)
        condition.subject = Patient(patient_id)
        delete_resource(resource=condition)

    results["diabetes_matched"] = True

    current_app.logger.debug(results)
    return results
