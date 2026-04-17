"""This module defines the router for all api routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException

import jwt

from OpenPostbud.routes.api import shipments
from OpenPostbud import config


security_scheme = HTTPBearer()


def check_bearer_token(credentials: HTTPAuthorizationCredentials=Depends(security_scheme)) -> dict[str, str]:
    """Check the validity of an incoming bearer JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, config.NICEGUI_STORAGE_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# Router object for all api routes
router = APIRouter(prefix="/api", dependencies=[Security(check_bearer_token)])
router.include_router(shipments.router)


@router.get("/hello", tags=["Test"], description="Used to test correct connection to the api.")
def get_hello(token: Annotated[dict[str, str], Depends(check_bearer_token)]):
    """Return a simple 'hello' response."""
    return {"response": "hello", "token": token}
