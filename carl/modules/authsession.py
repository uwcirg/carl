from flask import current_app
import requests
import time

from carl.config import (
    FHIR_CLIENT_ID,
    FHIR_CLIENT_SECRET,
    FHIR_SERVER_AUTH_URL,
)


def _fetch_token():
    headers = {"Content-Type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "client_id": FHIR_CLIENT_ID,
        "client_secret": FHIR_CLIENT_SECRET,
    }
    # verify=False supress SSL warnings like curl --insecure  (NOT ADVISED)
    current_app.logger.debug(f"token request to {FHIR_SERVER_AUTH_URL}")
    current_app.logger.debug(f"with headers: {headers} and data: {body}")
    response = requests.post(FHIR_SERVER_AUTH_URL, verify=False, headers=headers, data=body)
    current_app.logger.debug(f"response code: {response.status_code}")
    # response.raise_for_status()  insecure raises a 988
    current_app.logger.debug(f"text: {response.text}") 
    data = response.json()
    current_app.logger.debug(f"json: {data}") 
    assert data["token_type"] == "Bearer"
    return data["access_token"], data["expires_in"]


def dont_verify(**kwargs):
    updated_kwargs = dict(kwargs)
    updated_kwargs["verify"] = False
    return updated_kwargs


class AuthSession:
    _token = None
    _token_expiration = 0

    def __init__(self):
        self.session = requests.Session()

    def _update_token(self):
        now = time.time()
        if not AuthSession._token or now >= AuthSession._token_expiration:
            current_app.logger.debug("Fetch auth token")
            token, lifespan = _fetch_token()
            current_app.logger.debug(f"  obtained: {token}")
            AuthSession._token = token
            AuthSession._token_expiration = now + lifespan
        self.session.headers.update({
            "Authorization": f"Bearer {AuthSession._token}"}
        )

    def delete(self, url, **kwargs):
        self._update_token()
        current_app.logger.debug(f"make authorized DELETE request to {url}")
        updated_kwargs = dont_verify(**kwargs)
        return self.session.delete(url, **updated_kwargs)

    def get(self, url, **kwargs):
        self._update_token()
        current_app.logger.debug(f"make authorized GET request to {url}")
        updated_kwargs = dont_verify(**kwargs)
        return self.session.get(url, **updated_kwargs)

    def post(self, url, **kwargs):
        self._update_token()
        current_app.logger.debug(f"make authorized POST request to {url}")
        updated_kwargs = dont_verify(**kwargs)
        return self.session.post(url, **updated_kwargs)

    def put(self, url, **kwargs):
        self._update_token()
        current_app.logger.debug(f"make authorized PUT request to {url}")
        updated_kwargs = dont_verify(**kwargs)
        return self.session.put(url, **updated_kwargs)
