import json
import os

import requests
from flask import Blueprint, abort, current_app, jsonify
from flask.json import JSONEncoder

from carl.modules.factories import deserialize_resource

base_blueprint = Blueprint('base', __name__, cli_group=None)


@base_blueprint.before_app_first_request
def bootstrap():
    """Run application initialization code"""
    # Load serialized data into FHIR store
    fhir_url = current_app.config['FHIR_SERVER_URL']
    if not fhir_url:
        current_app.logger.warn("No config set for FHIR_SERVER_URL, can't load serialized data")
        return

    base_dir = os.path.join(current_app.root_path, "serialized")
    for fname in (fname for fname in os.scandir(base_dir) if fname.name.lower().endswith('.json')):
        with open(fname.path) as fhir:
            try:
                data = json.loads(fhir.read())
            except json.decoder.JSONDecodeError as je:
                current_app.logger.error(f"{fname.path} contains invalid JSON")
                current_app.logger.exception(je)

            endpoint = fhir_url
            if data['resourceType'] != 'Bundle':
                # For non bundles, PUT with search parameters to avoid
                # duplicate resource creation
                resource = deserialize_resource(data)
                endpoint += resource.search_url()

            current_app.logger.info(f"PUT {fname.name} to {endpoint}")
            response = requests.put(endpoint, json=data)
            current_app.logger.info(f"status {response.status_code}, text {response.text}")


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

