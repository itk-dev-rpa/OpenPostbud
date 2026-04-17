"""This module defines the token route for api jwt tokens."""

import time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Header, status
import jwt
from pydantic import BaseModel

from OpenPostbud import config
from OpenPostbud.database import api_users

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


@router.post("/token", tags=["Auth"])
def get_token(api_key: Annotated[str, Header(alias="API-key", pattern=r"[\w-]+\.[\w-]+")]) -> Token:
    """Exchange an API key for a JWT bearer token."""
    user = api_users.verify_api_key(api_key)

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid api key")

    payload = {
        "sub": user.id,
        "exp": int(time.time()) + config.API_TOKEN_LIFETIME_SECONDS,
        "iat": int(time.time()),
    }

    token = jwt.encode(payload, config.NICEGUI_STORAGE_SECRET, algorithm="HS256")

    return Token(access_token=token, token_type="bearer", expires_in=config.API_TOKEN_LIFETIME_SECONDS)
