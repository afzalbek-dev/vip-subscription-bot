"""Tests for DatabaseRepository CRUD and business queries."""

import pytest
from datetime import datetime, timedelta, timezone
from vip_bot.database.models import User, Payment


@pytest.mark.asyncio
async def test_init_and_plans_seeding(test_repo):
    """Verify default plans seeded upon initialization."""
    plans = await test_repo.get_plans()
    assert len(plans) >= 3
    plan_ids = [p.id for p in plans]
    assert "vip_30" in plan_ids
    assert "vip_90" in plan_ids
    assert "vip_365" in plan_ids


@pytest.mark.asyncio
async def test_user_operations(test_repo):
    """Verify user upsert and retrieval."""
    user = User(user_id=12345, username="testuser", full_name="Test User")
    await test_repo.upsert_user(user)

    fetched = await test_repo.get_user(12345)
    assert fetched is not None
    assert fetched.username == "testuser"
    assert fetched.full_name == "Test User"


@pytest.mark.asyncio
async def test_payment_operations(test_repo):
    """Verify payment creation and status updates."""
    payment = Payment(
        user_id=12345,
        plan_id="vip_30",
        amount=100000.0,
        currency="UZS",
        payment_method="payme",
        status="pending",
    )
    payment_id = await test_repo.create_payment(payment)
    assert payment_id > 0

    fetched = await test_repo.get_payment(payment_id)
    assert fetched.status == "pending"

    await test_repo.update_payment_status(payment_id, "approved", reviewed_by=999)
    updated = await test_repo.get_payment(payment_id)
    assert updated.status == "approved"
    assert updated.reviewed_by == 999


@pytest.mark.asyncio
async def test_subscription_creation_and_extension(test_repo):
    """Verify subscription creation and extending existing active period."""
    user_id = 55555
    # Create 30 days subscription
    sub1 = await test_repo.create_or_extend_subscription(user_id, "vip_30", duration_days=30)
    assert sub1.status == "active"
    assert sub1.end_date.timestamp() > (datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp()

    # Extend by another 30 days
    sub2 = await test_repo.create_or_extend_subscription(user_id, "vip_30", duration_days=30)
    assert sub2.end_date > sub1.end_date
    assert (sub2.end_date - sub1.start_date).days >= 59


@pytest.mark.asyncio
async def test_stats_metrics(test_repo):
    """Verify dashboard stats calculation."""
    await test_repo.upsert_user(User(user_id=1, full_name="U1"))
    await test_repo.upsert_user(User(user_id=2, full_name="U2"))
    await test_repo.create_or_extend_subscription(1, "vip_30", 30)

    stats = await test_repo.get_stats()
    assert stats["total_users"] >= 2
    assert stats["active_subs"] >= 1
