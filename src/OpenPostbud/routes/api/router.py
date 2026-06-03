"""This module defines the router for all api routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Security

from OpenPostbud.routes.api import shipments
from OpenPostbud.routes.api.dependencies import check_bearer_token, TokenData


# Router object for all api routes
router = APIRouter(prefix="/api", dependencies=[Security(check_bearer_token)])
router.include_router(shipments.router)


@router.get("/hello", tags=["Test"], description="Used to test correct connection to the api.")
def get_hello(token: Annotated[TokenData, Depends(check_bearer_token)]):
    """Return a simple 'hello' response."""
    return {"response": "hello", "token": token}
