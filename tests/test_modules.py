import json
import os
from pytest import fixture
from urllib.parse import urlencode

from carl.logic.copd import CNICS_COPD_coding
from carl.logic.diabetes import A1C_observation_coding
from carl.modules.factories import deserialize_resource
from carl.modules.codeableconcept import CodeableConcept
from carl.modules.coding import Coding
from carl.modules.condition import Condition
from carl.modules.codesystem import CodeSystem
from carl.modules.observation import Observation
from carl.modules.paging import next_page_link_from_bundle, next_resource_bundle
from carl.modules.patient import Patient, patient_canonical_identifier
from carl.modules.reference import Reference
from carl.modules.valueset import ValueSet, valueset_codings
from carl.modules.valuequantity import ValueQuantity

PATIENT_ID = "def123"


class MockResponse(object):
    """Wrap data in response like object"""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code == 200:
            return
        raise Exception("status code ain't 200")


def load_jsondata(datadir, filename):
    with open(os.path.join(datadir, filename), "r") as jsonfile:
        data = json.load(jsonfile)
    return data


@fixture
def codesystem_data(datadir):
    return load_jsondata(datadir, "codesystem.json")


@fixture
def copd_condition():
    cc = Condition()
    cc.code = CodeableConcept(CNICS_COPD_coding)
    cc.subject = Patient(PATIENT_ID)
    return cc


@fixture
def diabetes_observation():
    d = Observation()
    d.code = CodeableConcept(A1C_observation_coding)
    d.subject = Patient(PATIENT_ID)
    return d


@fixture
def diabetes_neg_observation(diabetes_observation):
    vq = ValueQuantity.from_fhir({
        "value": "4.95",
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%"})
    diabetes_observation.valuequantity = vq
    return diabetes_observation


@fixture
def diabetes_pos_observation(diabetes_observation):
    diabetes_observation.valuequantity = ValueQuantity.from_fhir({
        "value": 6.70,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%"
    })
    return diabetes_observation

@fixture
def patient_data(datadir):
    return load_jsondata(datadir, "patient.json")


@fixture
def patient_search_bundle(datadir):
    return load_jsondata(datadir, "patient_search.json")


@fixture
def valueset_bundle(datadir):
    return load_jsondata(datadir, "valueset_bundle.json")


@fixture
def valueset_data(datadir):
    return load_jsondata(datadir, "valueset.json")


def test_deserialize_codesystem(codesystem_data):
    resource = deserialize_resource(codesystem_data)
    assert isinstance(resource, CodeSystem)
    encoded_url = urlencode(query={"url": "http://hl7.org/fhir/sid/icd-10-cm"})
    assert resource.search_url() == f"CodeSystem?{encoded_url}"


def test_deserialize_valueset(valueset_data):
    resource = deserialize_resource(valueset_data)
    assert isinstance(resource, ValueSet)
    encoded_url = urlencode(
        query={
            "url": "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-codings"
        }
    )
    assert resource.search_url() == f"ValueSet?{encoded_url}"


def test_valueset_codings(mocker, valueset_bundle):

    # fake HAPI round trip call w/i valueset_codings()
    mocker.patch(
        "carl.modules.valueset.requests.get",
        return_value=MockResponse(data=valueset_bundle),
    )

    vs_url = "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-codings"
    codings = valueset_codings(vs_url)

    assert len(codings) == 30

    # Confirm a set including a known coding can be located
    look_for = set()
    look_for.add(Coding(system="http://snomed.info/sct", code="404684003"))

    assert look_for.intersection(codings)


def test_COPD_condition_patient(copd_condition):
    assert copd_condition.code == CodeableConcept(CNICS_COPD_coding)
    params = urlencode(
        {
            "code": f"{CNICS_COPD_coding.system}|{CNICS_COPD_coding.code}",
            "subject": PATIENT_ID,
        }
    )
    assert copd_condition.search_url() == f"Condition?{params}"


def test_diabetes_obs_patient(diabetes_observation):
    assert diabetes_observation.code == CodeableConcept(A1C_observation_coding)
    params = urlencode(
        {
            "code": f"{A1C_observation_coding.system}|{A1C_observation_coding.code}",
            "subject": PATIENT_ID
        }
    )
    assert diabetes_observation.search_url() == f"Observation?{params}"


def test_condition_as_fhir(copd_condition):
    fhir = copd_condition.as_fhir()
    assert set(fhir.keys()) == set(("resourceType", "code", "subject"))
    assert Reference(Patient(id=PATIENT_ID)).as_fhir() == fhir["subject"]


def test_paging(mocker, patient_search_bundle):

    # mock first of many page results:
    mocker.patch(
        "carl.modules.paging.requests.get",
        return_value=MockResponse(data=patient_search_bundle),
    )

    for bundle_page in next_resource_bundle("Patient"):
        assert "link" in bundle_page
        break  # only first page returned from mocker

    # obtain valid URL from bundle
    url = next_page_link_from_bundle(bundle_page)
    assert url.startswith("http://")


def test_canonical_identifier(mocker, patient_data):

    # mock HAPI result from patient lookup
    mocker.patch(
        "carl.modules.patient.requests.get", return_value=MockResponse(data=patient_data)
    )

    found = patient_canonical_identifier(patient_id=1, site_code="uw")
    assert found == "https://cnics.cirg.washington.edu/site-patient-id/uw|UW:517"


def test_diabetes_obs_pos_threshold(diabetes_pos_observation):
    assert diabetes_pos_observation.valuequantity.value == 6.5
    assert diabetes_pos_observation.valuequantity_above_threshold("6.0")
    assert not diabetes_pos_observation.valuequantity_above_threshold("9.0")


def test_diabetes_obs_pos_threshold(diabetes_neg_observation):
    assert float(diabetes_neg_observation.valuequantity.value) == 4.95
    assert not diabetes_neg_observation.valuequantity_above_threshold("6.0")
    assert diabetes_neg_observation.valuequantity_above_threshold("2.0")


def test_observation_serializers(diabetes_pos_observation):
    obs = Observation.from_fhir(diabetes_pos_observation.as_fhir())
    assert obs.code == diabetes_pos_observation.code
    assert obs.subject.as_fhir() == diabetes_pos_observation.subject.as_fhir()
    assert obs.valuequantity.as_fhir() == diabetes_pos_observation.valuequantity.as_fhir()
