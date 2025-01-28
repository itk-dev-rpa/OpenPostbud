"""This module defines the router for all user routes.
That is all routes that require a user to be logged in.
"""

from nicegui import APIRouter

from OpenPostbud.routes.user import send_post, tjek_tilmelding, forsendelser, front_page, opret_tilmelding


# Router object for all user routes
router = APIRouter(prefix="/user")

router.include_router(tjek_tilmelding.router)
router.include_router(send_post.router)
router.include_router(forsendelser.router)
router.include_router(front_page.router)
router.include_router(opret_tilmelding.router)
