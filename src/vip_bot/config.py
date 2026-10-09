"""Configuration management for VIP Subscription Bot."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """Application settings with environment variable fallbacks."""

    bot_token: str = Field(default_factory=lambda: os.getenv("BOT_TOKEN", "mock_bot_token_for_tests"))
    admin_ids: List[int] = Field(
        default_factory=lambda: [
            int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
        ]
    )
    vip_channel_id: int = Field(default_factory=lambda: int(os.getenv("VIP_CHANNEL_ID", "0")))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/vip_bot.db"))

    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # Background worker settings
    expiry_check_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("EXPIRY_CHECK_INTERVAL_SECONDS", "60"))
    )
    reminder_hours_before_expiry: int = Field(
        default_factory=lambda: int(os.getenv("REMINDER_HOURS_BEFORE_EXPIRY", "24"))
    )

    # Payment details (shown to user)
    payme_card: str = Field(default_factory=lambda: os.getenv("PAYME_CARD", "8600 0000 0000 0000"))
    click_card: str = Field(default_factory=lambda: os.getenv("CLICK_CARD", "8600 0000 0000 0000"))
    crypto_usdt_trc20: str = Field(
        default_factory=lambda: os.getenv("CRYPTO_USDT_TRC20", "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    )
    card_holder_name: str = Field(default_factory=lambda: os.getenv("CARD_HOLDER_NAME", "AFZALBEK D."))

    @property
    def sqlite_path(self) -> Path:
        """Extract Path from sqlite:/// URI or direct path."""
        uri = self.database_url
        if uri.startswith("sqlite:///"):
            uri = uri[len("sqlite:///"):]
        p = Path(uri)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def is_admin(self, user_id: int) -> bool:
        """Check if user is in configured administrators list."""
        return user_id in self.admin_ids


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached instance of application settings."""
    return Settings()
