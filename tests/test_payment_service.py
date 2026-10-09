"""Tests for PaymentService."""

import pytest
from vip_bot.database.models import User


@pytest.mark.asyncio
async def test_payment_service_flow(payment_service, test_repo):
    """Verify payment registration, approval, and rejection."""
    user = User(user_id=8888, full_name="Buyer")
    await test_repo.upsert_user(user)

    # Register payment
    pay_id = await payment_service.register_payment_submission(
        user_id=8888, plan_id="vip_30", method="payme", receipt_file_id="photo_123"
    )
    assert pay_id > 0

    # Approve
    approved = await payment_service.approve_payment(pay_id, admin_id=111)
    assert approved is not None
    assert approved.status == "approved"
    assert approved.reviewed_by == 111

    # Second approval attempt should return None (already processed)
    second_attempt = await payment_service.approve_payment(pay_id, admin_id=111)
    assert second_attempt is None


def test_payment_details_text(payment_service, test_settings):
    """Verify payment instructions text formatting."""
    from vip_bot.database.models import Plan
    plan = Plan("vip_30", "VIP 1 Month", 30, 100000, 8.0)
    text = payment_service.get_payment_details_text(plan, "payme")
    assert "100,000 so'm" in text
    assert test_settings.payme_card in text
