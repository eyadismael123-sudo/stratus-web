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

    # Telegram bots (one per agent)
    telegram_bot_token_brief: str = ""
    telegram_bot_token_linkedin: str = ""
    telegram_bot_token: str = ""  # legacy fallback — prefer the per-agent tokens above

    # WhatsApp Cloud API (Meta)
    whatsapp_access_token: str = ""       # permanent system user token
    whatsapp_phone_number_id: str = ""    # Meta phone number ID
    whatsapp_verify_token: str = ""       # arbitrary string you set in Meta dashboard
    whatsapp_app_secret: str = ""         # for HMAC-SHA256 signature verification

    # Grok API (xAI — real-time X/Twitter signals)
    grok_api_key: str = ""

    # LinkedIn Ghostwriter OAuth
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/linkedin/oauth/callback"

    # App
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
