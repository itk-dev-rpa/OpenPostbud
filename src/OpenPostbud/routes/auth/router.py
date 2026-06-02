"""This module defines the router for all auth routes."""

from nicegui import APIRouter

from OpenPostbud.routes.auth import admin_login, login, token

# Router object for all auth routes
router = APIRouter(prefix="/auth")

router.include_router(admin_login.router, include_in_schema=False)
router.include_router(login.router, include_in_schema=False)
router.include_router(token.router)
