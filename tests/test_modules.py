import json
import os
from pytest import fixture
from urllib.parse import urlencode

from carl.modules.factories import deserialize_resource
from carl.modules.codesystem import CodeSystem
from carl.modules.valueset import ValueSet


def load_jsondata(datadir, filename):
    with open(os.path.join(datadir, filename), 'r') as jsonfile:
        data = json.load(jsonfile)
    return data


@fixture
def codesystem_data(datadir):
    return load_jsondata(datadir, 'codesystem.json')


@fixture
def valueset_data(datadir):
    return load_jsondata(datadir, 'valueset.json')


def test_deserialize_codesystem(codesystem_data):
    resource = deserialize_resource(codesystem_data)
    assert isinstance(resource, CodeSystem)
    encoded_url = urlencode(query={'url': "http://hl7.org/fhir/sid/icd-10-cm"})
    assert resource.search_url() == f'CodeSystem?{encoded_url}'


def test_deserialize_valueset(valueset_data):
    resource = deserialize_resource(valueset_data)
    assert isinstance(resource, ValueSet)
    encoded_url = urlencode(query={'url': "http://cnics-cirg.washington.edu/fhir/ValueSet/CNICS-COPD-codings"})
    assert resource.search_url() == f'ValueSet?{encoded_url}'
