"""This module defines the router for all api routes."""

from fastapi import APIRouter, Security, status
from fastapi.security import APIKeyHeader
from fastapi.exceptions import HTTPException

from OpenPostbud.database import api_users
from OpenPostbud.routes.api import shipments


security_scheme = APIKeyHeader(name="X-API-key")

def check_api_key(api_key: str = Security(security_scheme)):
    """Check for a valid api key."""
    if not api_users.verify_api_key(api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid api key")


# Router object for all api routes
router = APIRouter(prefix="/api", dependencies=[Security(check_api_key)])
router.include_router(shipments.router)

@router.get("/hello", tags=["Test"], description="Used to test correct connection to the api.")
def get_hello():
    """Return a simple 'hello' response."""
    return {"response": "hello"}

