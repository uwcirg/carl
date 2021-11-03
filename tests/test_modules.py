import json
import os
from pytest import fixture

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
    assert resource.search_url() == 'CodeSystem?url=http%3A%2F%2Fhl7.org%2Ffhir%2Fsid%2Ficd-10-cm'


def test_deserialize_valueset(valueset_data):
    resource = deserialize_resource(valueset_data)
    assert isinstance(resource, ValueSet)
    assert resource.search_url() == 'ValueSet?url=http%3A%2F%2Fcnics-cirg.washington.edu%2Ffhir%2FValueSet%2FCNICS-COPD-codings'
