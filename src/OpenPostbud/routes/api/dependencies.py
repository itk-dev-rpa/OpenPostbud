"""This module contains shared dependencies for the api routes."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

import jwt

from OpenPostbud import config


security_scheme = HTTPBearer()


class TokenData(BaseModel):
    """The decoded payload of an api bearer token."""
    sub: str
    group: str
    exp: int
    iat: int


def check_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> TokenData:
    """Check the validity of an incoming bearer JWT token."""
    try:
        payload = jwt.decode(credentials.credentials, config.API_JWT_SECRET, algorithms=["HS256"])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")  # pylint: disable=raise-missing-from
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")  # pylint: disable=raise-missing-from
