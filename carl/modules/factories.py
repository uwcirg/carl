"""Factories to instantiate resources using runtime values"""
from carl.modules.codesystem import CodeSystem
from carl.modules.valueset import ValueSet


def deserialize_resource(data):
    """Given JSON data representation of FHIR Resource, return instance"""
    # Cycle through known resource classes, looking for match to instantiate
    resource = None
    for cls in CodeSystem, ValueSet:
        if cls.RESOURCE_TYPE == data["resourceType"]:
            assert resource is None
            resource = cls.from_fhir(data)

    if resource is None:
        raise ValueError(f"FHIR resource f{data['resourceType']} class not found")

    return resource
