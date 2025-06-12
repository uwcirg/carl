import requests
import time

from carl.config import FHIR_CLIENT_SECRET, FHIR_SERVER_URL


def _fetch_token():
    auth_path = "/".join((FHIR_SERVER_URL, "auth/token"))
    headers = {"Content-Type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "client_id": FHIR_CLIENT_SECRET,
        "client_secret": FHIR_CLIENT_SECRET,
    }
    # verify=False supress SSL warnings like curl --insecure  (NOT ADVISED)
    response = requests.get(auth_path, verify=False, headers=headers, data=body)
    response.raise_for_status()
    data = response.json()
    assert data["token_type"] == "Bearer"
    return data["access_token"], data["expires_in"]


class AuthSession:
    _token = None
    _token_expiration = 0

    def __init__(self):
        self.session = requests.Session()
        self._update_token()

    def _update_token(self):
        now = time.time()
        if not AuthSession._token or now >= AuthSession._token_expiration:
            token, lifespan = _fetch_token()
            AuthSession._token = token
            AuthSession._token_expiration = now + lifespan
        self.session.headers.update({
            "Authorization": f"Bearer {AuthSession._token}"}
        )

    def delete(self, url, **kwargs):
        self._update_token()
        return self.session.delete(url, **kwargs)

    def get(self, url, **kwargs):
        self._update_token()
        return self.session.get(url, **kwargs)

    def post(self, url, **kwargs):
        self._update_token()
        return self.session.post(url, **kwargs)

    def put(self, url, **kwargs):
        self._update_token()
        return self.session.put(url, **kwargs)
