"""This module defines the router for all auth routes."""

from nicegui import APIRouter

from OpenPostbud.routes.auth import admin_login, login

# Router object for all auth routes
router = APIRouter(prefix="/auth", include_in_schema=False)

router.include_router(admin_login.router)
router.include_router(login.router)
