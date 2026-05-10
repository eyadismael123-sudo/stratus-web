"""Stratus FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, agents, auth, chat, health, marketplace, subscriptions, waitlist, webhooks
from app.api import linkedin, whatsapp_webhook, telegram_webhook
from app.agents.brief.scheduler import start_scheduler, stop_scheduler
from app.agents.linkedin.scheduler import start_linkedin_scheduler, stop_linkedin_scheduler
from app.config import settings
from app.exceptions import AppError, app_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    start_linkedin_scheduler()
    yield
    stop_scheduler()
    stop_linkedin_scheduler()


app = FastAPI(
    title="Stratus API",
    description="Your AI workforce. Built for Dubai. Hired by the month.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
app.add_exception_handler(AppError, app_error_handler)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(marketplace.router)
app.include_router(agents.router)
app.include_router(subscriptions.router)
app.include_router(webhooks.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(waitlist.router)
app.include_router(whatsapp_webhook.router)
app.include_router(telegram_webhook.router)
app.include_router(linkedin.router)
