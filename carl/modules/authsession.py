from flask import current_app
import requests
import time

from carl.config import (
    FHIR_CLIENT_ID,
    FHIR_CLIENT_SECRET,
    FHIR_SERVER_AUTH_URL,
    FHIR_SERVER_IGNORE_CERT,
)


def _fetch_token():
    headers = {"Content-Type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "client_id": FHIR_CLIENT_ID,
        "client_secret": FHIR_CLIENT_SECRET,
    }
    verify = not FHIR_SERVER_IGNORE_CERT
    response = requests.post(FHIR_SERVER_AUTH_URL, verify=verify, headers=headers, json=body)
    response.raise_for_status()
    data = response.json()
    assert data["token_type"] == "Bearer"
    return data["access_token"], data["expires_in"]


def dont_verify(**kwargs):
    """Add verify=False parameter when server doesn't have valid certificate"""
    if not FHIR_SERVER_IGNORE_CERT:
        return kwargs
    updated_kwargs = dict(kwargs)
    updated_kwargs["verify"] = False
    return updated_kwargs


class AuthSession:
    _token = None
    _token_expiration = 0

    def __init__(self):
        self.session = requests.Session()

    def _update_token(self):
        if not FHIR_SERVER_AUTH_URL:
            # Ignore token need on servers without a configured AUTH_URL
            return

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
        updated_kwargs = dont_verify(**kwargs)
        return self.session.delete(url, **updated_kwargs)

    def get(self, url, **kwargs):
        self._update_token()
        updated_kwargs = dont_verify(**kwargs)
        return self.session.get(url, **updated_kwargs)

    def post(self, url, **kwargs):
        self._update_token()
        updated_kwargs = dont_verify(**kwargs)
        return self.session.post(url, **updated_kwargs)

    def put(self, url, **kwargs):
        self._update_token()
        updated_kwargs = dont_verify(**kwargs)
        return self.session.put(url, **updated_kwargs)
