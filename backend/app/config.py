"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Anthropic
    anthropic_api_key: str = ""

    # Stripe (optional until Stripe account is set up)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # Google Sheets (waitlist)
    google_service_account_json: str = ""  # full JSON string from service account key file
    google_sheet_id: str = ""  # ID from the Sheet URL

    # News (Doctor Morning Briefing)
    news_api_key: str = ""  # newsapi.org — free tier: 100 req/day

    # Telegram (agent delivery — legacy, superseded by WhatsApp)
    telegram_bot_token: str = ""

    # WhatsApp Cloud API (Meta)
    whatsapp_access_token: str = ""       # permanent system user token
    whatsapp_phone_number_id: str = ""    # Meta phone number ID
    whatsapp_verify_token: str = ""       # arbitrary string you set in Meta dashboard
    whatsapp_app_secret: str = ""         # for HMAC-SHA256 signature verification

    # Grok API (xAI — real-time X/Twitter clinical signals)
    grok_api_key: str = ""

    # 3D Print API v1
    print3d_api_keys: str = ""           # comma-separated valid API keys
    shopify_webhook_secret: str = ""     # HMAC secret for order.paid webhooks from cousin's app
    model_url_signing_key: str = ""      # secret for signing modelUrl query params
    rate_limit_per_minute: int = 30      # per customer_id
    signed_url_ttl_minutes: int = 30     # lifetime of signed modelUrl

    # App
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"
    api_base_url: str = "http://localhost:8000"  # used to build absolute modelUrl in /v1 responses

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
