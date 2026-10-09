"""Tests for ExpiryWorker."""

import pytest
import aiosqlite
from datetime import datetime, timedelta, timezone
from vip_bot.workers.expiry_worker import ExpiryWorker


@pytest.mark.asyncio
async def test_expiry_worker_reminders_and_revocations(
    test_settings, test_repo, channel_service, mock_bot
):
    """Verify 24h reminder notification and automatic member revocation upon expiry."""
    worker = ExpiryWorker(test_settings, test_repo, channel_service)

    # 1. User with subscription expiring in 5 hours (needs reminder)
    sub_expiring = await test_repo.create_or_extend_subscription(user_id=101, plan_id="vip_30", duration_days=30)
    
    # Backdate end_date to 5 hours from now
    async with aiosqlite.connect(test_repo.db_path) as db:
        new_end = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()
        await db.execute("UPDATE subscriptions SET end_date = ? WHERE id = ?", (new_end, sub_expiring.id))
        await db.commit()

    reminders_sent = await worker.process_expiring_reminders(mock_bot)
    assert reminders_sent >= 1
    mock_bot.send_message.assert_awaited()

    # 2. User with already expired subscription
    sub_expired = await test_repo.create_or_extend_subscription(user_id=202, plan_id="vip_30", duration_days=30)
    async with aiosqlite.connect(test_repo.db_path) as db:
        past_end = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        await db.execute("UPDATE subscriptions SET end_date = ? WHERE id = ?", (past_end, sub_expired.id))
        await db.commit()

    revoked_count = await worker.process_expired_revocations(mock_bot)
    assert revoked_count >= 1
    mock_bot.ban_chat_member.assert_awaited()
    mock_bot.unban_chat_member.assert_awaited()
