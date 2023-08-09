import click
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, abort, current_app, jsonify
from flask.json import JSONEncoder
import json
from operator import itemgetter
import timeit

from carl.logic.copd import classify_for_COPD, remove_COPD_classification
from carl.logic.diabetes import classify_for_diabetes, remove_diabetes_classification
from carl.modules.patient import CNICS_IDENTIFIER_SYSTEM
from carl.modules.paging import next_resource_bundle

base_blueprint = Blueprint("base", __name__, cli_group=None)


@base_blueprint.cli.command("bootstrap")
def bootstrap():
    """Run application initialization code"""
    # Load serialized data into FHIR store
    from carl.serialized.upload import load_files

    load_files()


@base_blueprint.route("/")
def root():
    return {"message": "ok"}


@base_blueprint.route("/settings", defaults={"config_key": None})
@base_blueprint.route("/settings/<string:config_key>")
def config_settings(config_key):
    """Non-secret application settings"""

    # workaround no JSON representation for datetime.timedelta
    class CustomJSONEncoder(JSONEncoder):
        def default(self, obj):
            return str(obj)

    current_app.json_encoder = CustomJSONEncoder

    # return selective keys - not all can be be viewed by users, e.g.secret key
    blacklist = ("SECRET", "KEY")

    if config_key:
        key = config_key.upper()
        for pattern in blacklist:
            if pattern in key:
                abort(status_code=400, messag=f"Configuration key {key} not available")
        return jsonify({key: current_app.config.get(key)})

    settings = {}
    for key in current_app.config:
        matches = any(pattern for pattern in blacklist if pattern in key)
        if matches:
            continue
        settings[key] = current_app.config.get(key)

    return jsonify(settings)


@base_blueprint.route("/classify/<int:patient_id>", methods=["PUT"])
def classify(patient_id):
    """Classify single patient as configured"""
    results = classify_for_COPD(patient_id)
    results.update(classify_for_diabetes(patient_id))
    return results


@base_blueprint.cli.command("classify")
@click.argument("site", nargs=-1)
def classify_all(site):
    """Classify all patients found"""
    return process_patients(
        process_functions=(classify_for_COPD, classify_for_diabetes),
        site=site,
    )


@base_blueprint.cli.command("declassify")
@click.argument("site", nargs=-1)
def declassify_all(site):
    """Clear the (potentially) persisted conditions generated during classify"""
    return process_patients(
        (remove_COPD_classification, remove_diabetes_classification), site
    )


def process_patients(process_functions, site):
    """
    Process all patients for given site, with given list of functions.

    :param process_functions: ordered list of functions to call on each respective patient
    :param site: name of site being processed, i.e. "uw", or None for all sites
    """
    start = timeit.default_timer()
    # Obtain batches of Patients (with site identifier if requested),
    # process each in turn
    processed_patients = 0
    matched_patients = 0
    search_params = None
    patient_identifier_system = None
    if site:
        patient_identifier_system = CNICS_IDENTIFIER_SYSTEM + site
        # To query on system portion only of an identifier, must include
        # trailing '|' used customarily to delimit `system|value`
        search_params = {"identifier": patient_identifier_system + "|"}

    for bundle in next_resource_bundle("Patient", search_params=search_params):
        assert bundle["resourceType"] == "Bundle"
        for item in bundle.get("entry", []):
            assert item["resource"]["resourceType"] == "Patient"
            results = dict()
            for process_function in process_functions:
                results.update(process_function(item["resource"]["id"]))
            processed_patients += 1
            if any(key.endswith("matched") for key in results.keys()):
                matched_patients += 1

    duration = timeit.default_timer() - start
    click.echo(
        {
            "duration": f"{duration:.4f} seconds",
            "patient_identifier_system": patient_identifier_system,
            "processed_patients": processed_patients,
            "matched_patients": matched_patients,
        }
    )


@base_blueprint.cli.command("valueset")
@click.argument("resource_type")
@click.argument("description")
def generate_valueset(resource_type, description):
    """Generate valueset of all given resources of requested type found"""
    seen = set()
    results = defaultdict(list)
    for bundle in next_resource_bundle(resource_type, search_params={"_count": 500}):
        for item in bundle.get("entry", []):
            assert item["resource"]["resourceType"] == resource_type
            assert len(item["resource"]["code"]["coding"]) == 1
            system = item["resource"]["code"]["coding"][0]["system"]
            code = item["resource"]["code"]["coding"][0]["code"]

            # Organize as needed for ValueSets, i.e. by system

            # prune out duplicates - i.e. when same resource is assigned
            # to hundreds of patients
            key = "|".join((system, code))
            if key in seen:
                continue
            seen.add(key)
            display = item["resource"]["code"]["coding"][0]["display"]
            results[system].append({"code": code, "display": display})

    # repackage results for valueset
    include = []
    for system in results.keys():
        include.append(
            {
                "system": system,
                "concept": [v for v in sorted(results[system], key=itemgetter("code"))],
            }
        )

    valueset = {
        "resourceType": "ValueSet",
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/shareablevalueset"]
        },
        "text": {
            "status": "generated",
            "div": '<div xmlns="http://www.w3.org/1999/xhtml">\n\t\t\t'
            f"<p>Value set &quot;CNICS ValueSet for {description}&quot;</p>\n\t\t\t"
            "<p>Developed by: CIRG</p>\n\t\t</div>",
        },
        "url": "http://cnics-cirg.washington.edu/"
        f"fhir/ValueSet/CNICS-{description.replace(' ', '-')}",
        "identifier": [
            {
                "system": "http://cnics-cirg.washington.edu/fhir/identifier/valueset",
                "value": f"CNICS-{description}",
            }
        ],
        "version": datetime.now().strftime("%Y%m%d"),
        "name": f"CNICS {description}",
        "status": "draft",
        "experimental": True,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "publisher": "CIRG",
        "contact": [
            {
                "name": "CIRG project team",
                "telecom": [
                    {"system": "url", "value": "https://www.cirg.washington.edu/"}
                ],
            }
        ],
        "description": f"ValueSet including all the codings used by CNICS to define {description}",
        "compose": {
            "lockedDate": datetime.now().strftime("%Y-%m-%d"),
            "include": include,
        },
    }

    print(json.dumps(valueset, indent=2))
