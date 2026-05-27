"""v1 API router — assembles all /v1/* sub-routers."""
from fastapi import APIRouter

from app.api.v1 import health, chat, generate, download, webhooks, models as models_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(health.router)
v1_router.include_router(chat.router)
v1_router.include_router(generate.router)
v1_router.include_router(download.router)
v1_router.include_router(webhooks.router)
v1_router.include_router(models_router.router)
