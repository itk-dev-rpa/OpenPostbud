"""Shared FastAPI dependencies for the api routes."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException

import jwt

from OpenPostbud import config


security_scheme = HTTPBearer()


def check_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict[str, str]:
    """Check the validity of an incoming bearer JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, config.API_JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")  # pylint: disable=raise-missing-from
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")  # pylint: disable=raise-missing-from
