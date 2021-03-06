import click
from flask import Blueprint, abort, current_app, jsonify
from flask.json import JSONEncoder
import timeit

from carl.logic.copd import (
    CNICS_IDENTIFIER_SYSTEM,
    process_4_COPD_conditions,
    process_4_COPD_medications,
    remove_COPD_classification,
)
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


@base_blueprint.route("/classify/<int:patient_id>/<string:site_code>", methods=["PUT"])
def classify(patient_id, site_code):
    """Classify single patient as configured"""
    results = dict()
    results["Condition"] = process_4_COPD_conditions(patient_id, site_code)
    # We only consider COPD meds if the patient obtained the COPD condition
    if results["Condition"]["matched"]:
        results["MedicationRequest"] = process_4_COPD_medications(patient_id, site_code)
    return results


@base_blueprint.cli.command("classify")
@click.argument("site")
def classify_all(site):
    """Classify all patients found"""
    return process_patients(
        process_functions=(process_4_COPD_conditions, process_4_COPD_medications),
        site=site,
        require_all=True,
    )


@base_blueprint.cli.command("declassify")
@click.argument("site")
def declassify_all(site):
    """Clear the (potentially) persisted COPD condition generated during classify"""
    return process_patients((remove_COPD_classification,), site)


def process_patients(process_functions, site, require_all=False):
    """
    Process all patients with given list of functions.

    :param process_functions: ordered list of functions to call on each respective patient
    :param site: name of site being processed, i.e. "uw"
    :param require_all: set True to treat ordered list of process functions with a logical
      AND, i.e. bail on each patient with first function in list to fail
    """
    start = timeit.default_timer()
    results = dict()
    # Obtain batches of Patients with site identifier, process each in turn
    processed_patients = 0
    matched_patients = 0
    patient_identifier_system = CNICS_IDENTIFIER_SYSTEM + site
    # To query on system portion only of an identifier, must include
    # trailing '|' used customarily to delimit `system|value`
    search_params = {"identifier": patient_identifier_system + "|"}
    for bundle in next_resource_bundle("Patient", search_params=search_params):
        assert bundle["resourceType"] == "Bundle"
        for item in bundle.get("entry", []):
            matched = False
            assert item["resource"]["resourceType"] == "Patient"
            for process_function in process_functions:
                results = process_function(
                    patient_id=item["resource"]["id"], site_code=site
                )
                matched = matched or results.get("matched", False)
                if require_all and not matched:
                    break
            processed_patients += 1
            if matched:
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
