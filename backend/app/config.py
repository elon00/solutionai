import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    # API Settings
    app_name: str = "Solution AI Ticket Triage SaaS"
    version: str = "1.0.0"
    description: str = "AI-powered ticket classification and triage system"

    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://solution_user:solution_pass@localhost:5432/solution_ai")

    # AI Providers
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    allowed_api_keys: List[str] = os.getenv("ALLOWED_API_KEYS", "demo_key_123").split(",")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@solutionai.com")

    # Observability
    jaeger_host: str = os.getenv("JAEGER_HOST", "jaeger")
    jaeger_port: int = int(os.getenv("JAEGER_PORT", "6831"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "86400"))  # 24 hours

    # Features
    enable_caching: bool = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    enable_tracing: bool = os.getenv("ENABLE_TRACING", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()