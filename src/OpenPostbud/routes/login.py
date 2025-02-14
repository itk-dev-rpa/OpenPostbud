from typing import Optional
import os
import uuid

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from nicegui import app, ui
import dotenv
import requests
import jwt
from jwt.algorithms import RSAAlgorithm

from OpenPostbud import ui_components
from OpenPostbud.middleware import authentication

dotenv.load_dotenv()

CLIENT_ID = os.environ["client_id"]
CLIENT_SECRET = os.environ["client_secret"]
DISCOVERY_URL = os.environ["discovery_url"]
REDIRECT_URL = os.environ["redirect_url"]


@ui.page("/login", name="Login")
def login_page() -> Optional[RedirectResponse]:
    """Page shown to the user before logging in."""
    if authentication.is_authenticated():
        return RedirectResponse(app.url_path_for("Front Page"))

    ui_components.theme()

    with ui.card().classes('absolute-center'), ui.column(align_items='center'):
        ui.label("📯OpenPostbud📯").classes("text-2xl")
        ui.label("Klik på knappen for at blive omstillet til Single sign-on.")
        ui.button("Login", on_click=begin_login)


def begin_login():
    """Initiate auth code flow and redirect the user to the auth url."""
    auth_url = _get_discovery_data()["authorization_endpoint"]
    state = str(uuid.uuid4())
    app.storage.user["oidc_state"] = state

    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URL,
        'scope': 'openid',
        'state': state
    }

    req = requests.PreparedRequest()
    req.prepare_url(auth_url, params)

    ui.navigate.to(req.url)


@ui.page("/auth/callback")
def auth_page(code: str, state: str):
    """Callback url for OIDC.
    Use received auth code to acquire id token.
    """
    _validate_state(state)

    discovery_data = _get_discovery_data()
    token_url = discovery_data["token_endpoint"]

    token_response = requests.post(
        token_url,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URL,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
    )

    token_data = token_response.json()
    token = token_data.get("id_token")
    data = _decode_jwt(token, discovery_data)

    authentication.authenticate(data["upn"], data["role"])

    return RedirectResponse(app.storage.user.get('referer_path', app.url_path_for("Front Page")))


def _get_discovery_data() -> dict[str, str]:
    """Use the discovery URL to get information about the OIDC provider."""
    result = requests.get(DISCOVERY_URL)
    return result.json()


def _decode_jwt(token: str, discovery_data: dict) -> dict[str, str]:
    """Verify and decode a JWT token using the JWKS from the discovery url."""
    jwks_url = discovery_data["jwks_uri"]
    algorithms = discovery_data["id_token_signing_alg_values_supported"]
    jwks = requests.get(jwks_url).json()

    # Get the correct key from the jwks
    kid = jwt.get_unverified_header(token)["kid"]
    key = next(k for k in jwks["keys"] if k["kid"] == kid)

    public_key = RSAAlgorithm.from_jwk(key)
    return jwt.decode(token, public_key, algorithms=algorithms, audience=CLIENT_ID, leeway=10)


def _validate_state(state: str):
    """Validate a incoming state value to
    the one in the user's session storage.
    Deletes the state from the session to prevent reuse.

    Args:
        state: The state value to validate.

    Raises:
        HTTPException: If the states don't match.
    """
    if state != app.storage.user["oidc_state"]:
        raise HTTPException(400, "Invalid OIDC state in response")

    del app.storage.user["oidc_state"]
