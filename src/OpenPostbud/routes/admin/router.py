"""This module defines the router for all admin routes.
That is all routes that require an admin to be logged in.
"""

from nicegui import APIRouter

from OpenPostbud.routes.admin import api_users


# Router object for all admin routes
router = APIRouter(prefix="/admin", include_in_schema=False)

router.include_router(api_users.router)

