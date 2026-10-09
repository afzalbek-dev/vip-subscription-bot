"""Data models for VIP Subscription Bot."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    """Telegram User record."""
    user_id: int
    username: Optional[str] = None
    full_name: str = ""
    created_at: datetime = field(default_factory=get_utc_now)


@dataclass
class Plan:
    """Subscription plan details."""
    id: str
    name: str
    duration_days: int
    price_uzs: int
    price_usd: float
    description: str = ""
    is_active: bool = True


@dataclass
class Subscription:
    """Active or historical VIP subscription."""
    id: Optional[int] = None
    user_id: int = 0
    plan_id: str = ""
    start_date: datetime = field(default_factory=get_utc_now)
    end_date: datetime = field(default_factory=get_utc_now)
    status: str = "active"  # active, expired, revoked
    reminder_sent: bool = False


@dataclass
class Payment:
    """Payment record."""
    id: Optional[int] = None
    user_id: int = 0
    plan_id: str = ""
    amount: float = 0.0
    currency: str = "UZS"
    payment_method: str = "card"  # card, payme, click, crypto
    status: str = "pending"  # pending, approved, rejected
    receipt_file_id: Optional[str] = None
    created_at: datetime = field(default_factory=get_utc_now)
    reviewed_by: Optional[int] = None
