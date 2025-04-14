# Routes package
from arcade.api.routes.admin_pic_perfect import router as pic_perfect_admin_router
from arcade.api.routes.pic_perfect import router as pic_perfect_router
from arcade.api.routes.admin_pubg import router as pubg_admin_router
from arcade.api.routes.pubg import router as pubg_router
from arcade.api.routes.teams import router as teams_router

__all__ = [
    "pubg_admin_router",
    "pubg_router",
    "pic_perfect_router",
    "pic_perfect_admin_router",
    "teams_router",
]
