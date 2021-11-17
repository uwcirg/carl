import click
from flask import Blueprint, abort, current_app, jsonify
from flask.json import JSONEncoder
import timeit

from carl.logic.copd import process_4_COPD
from carl.modules.paging import next_resource_bundle

base_blueprint = Blueprint('base', __name__, cli_group=None)


@base_blueprint.before_app_first_request
def bootstrap():
    """Run application initialization code"""
    # Load serialized data into FHIR store
    from carl.serialized.upload import load_files
    load_files()


@base_blueprint.route('/')
def root():
    return {"message": "ok"}


@base_blueprint.route('/settings', defaults={'config_key': None})
@base_blueprint.route('/settings/<string:config_key>')
def config_settings(config_key):
    """Non-secret application settings"""

    # workaround no JSON representation for datetime.timedelta
    class CustomJSONEncoder(JSONEncoder):
        def default(self, obj):
            return str(obj)
    current_app.json_encoder = CustomJSONEncoder

    # return selective keys - not all can be be viewed by users, e.g.secret key
    blacklist = ('SECRET', 'KEY')

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


@base_blueprint.route('/classify/<int:patient_id>', methods=['PUT'])
def classify(patient_id):
    """Classify single patient as configured"""
    return process_4_COPD(patient_id)


@base_blueprint.cli.command("classify")
def classify_all():
    """Classify all patients found"""
    start = timeit.default_timer()

    # Obtain batches of Patients, process each in turn
    processed_patients = 0
    conditioned_patients = 0
    for bundle in next_resource_bundle('Patient'):
        assert bundle['resourceType'] == 'Bundle'
        for item in bundle.get('entry', []):
            assert item['resource']['resourceType'] == 'Patient'
            results = process_4_COPD(item['resource']['id'])
            processed_patients += 1
            if 'condition' in results:
                conditioned_patients += 1

    duration = timeit.default_timer() - start
    click.echo({
        'duration': f"{duration:.4f} seconds",
        'processed_patients': processed_patients,
        'conditioned_patients': conditioned_patients})
