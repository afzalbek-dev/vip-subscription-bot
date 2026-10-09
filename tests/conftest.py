"""Pytest fixtures for VIP Subscription Bot."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from vip_bot.config import Settings
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.channel_service import ChannelService
from vip_bot.services.payment_service import PaymentService
from vip_bot.services.subscription_service import SubscriptionService


@pytest.fixture
def temp_db_path():
    """Create a temporary SQLite database path."""
    tmpdir = tempfile.mkdtemp(prefix="test_vip_bot_")
    db_file = Path(tmpdir) / "test.db"
    yield db_file
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def test_settings(temp_db_path):
    """Provide isolated test settings."""
    return Settings(
        bot_token="123456:mock_token_for_unit_tests",
        admin_ids=[111, 222],
        vip_channel_id=-1001234567890,
        database_url=f"sqlite:///{temp_db_path}",
        app_env="test",
        expiry_check_interval_seconds=1,
        reminder_hours_before_expiry=24,
    )


@pytest.fixture
async def test_repo(temp_db_path):
    """Provide initialized DatabaseRepository."""
    repo = DatabaseRepository(temp_db_path)
    await repo.init_db()
    return repo


@pytest.fixture
def mock_bot():
    """Provide mocked Aiogram Bot."""
    bot = MagicMock()
    bot.create_chat_invite_link = AsyncMock(return_value=MagicMock(invite_link="https://t.me/+test_one_time_link"))
    bot.ban_chat_member = AsyncMock(return_value=True)
    bot.unban_chat_member = AsyncMock(return_value=True)
    bot.send_message = AsyncMock(return_value=MagicMock())
    bot.send_photo = AsyncMock(return_value=MagicMock())
    return bot


@pytest.fixture
def channel_service(test_settings):
    return ChannelService(test_settings.vip_channel_id)


@pytest.fixture
def payment_service(test_settings, test_repo):
    return PaymentService(test_settings, test_repo)


@pytest.fixture
def sub_service(test_repo, channel_service):
    return SubscriptionService(test_repo, channel_service)
