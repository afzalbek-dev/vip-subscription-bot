"""Tests for SubscriptionService."""

import pytest


@pytest.mark.asyncio
async def test_grant_subscription(sub_service, mock_bot):
    """Verify subscription grant and link generation."""
    user_id = 9999
    sub, link = await sub_service.grant_subscription(mock_bot, user_id=user_id, plan_id="vip_30")

    assert sub.user_id == user_id
    assert sub.status == "active"
    assert link == "https://t.me/+test_one_time_link"

    # Status check
    active_sub = await sub_service.check_user_status(user_id)
    assert active_sub is not None
    assert active_sub.id == sub.id
