"""Payment workflow service supporting Card, Click, Payme, and Crypto."""

import logging
from typing import Optional
from vip_bot.config import Settings
from vip_bot.database.models import Payment, Plan
from vip_bot.database.repository import DatabaseRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """Handles invoice generation and payment approval lifecycles."""

    def __init__(self, settings: Settings, repo: DatabaseRepository):
        self.settings = settings
        self.repo = repo

    def get_payment_details_text(self, plan: Plan, method: str) -> str:
        """Format payment requisites instructions for the selected method."""
        if method == "crypto":
            return (
                f"💎 *{plan.name} uchun To'lov (USDT TRC-20)*\n\n"
                f"💵 *Summa:* `{plan.price_usd} USDT`\n"
                f"🔗 *Hamyon (TRC-20):* `{self.settings.crypto_usdt_trc20}`\n\n"
                f"⚠️ *Muhim:* To'lovni amalga oshirgach, tranzaksiya skrinshoti yoki TXID chekini shu botga yuboring."
            )
        else:
            card = self.settings.payme_card if method == "payme" else self.settings.click_card
            return (
                f"💎 *{plan.name} uchun To'lov ({method.upper()})*\n\n"
                f"💰 *Summa:* `{plan.price_uzs:,} so'm`\n"
                f"💳 *Karta raqami:* `{card}`\n"
                f"👤 *Qabul qiluvchi:* `{self.settings.card_holder_name}`\n\n"
                f"⚠️ *Muhim:* To'lovni amalga oshirgach, chek / kvitansiya skrinshotini shu botga rasm sifatida yuboring."
            )

    async def register_payment_submission(
        self, user_id: int, plan_id: str, method: str, receipt_file_id: Optional[str]
    ) -> int:
        """Register a user's submitted receipt and return payment ID."""
        plan = await self.repo.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan '{plan_id}' does not exist")

        amount = plan.price_usd if method == "crypto" else plan.price_uzs
        currency = "USDT" if method == "crypto" else "UZS"

        payment = Payment(
            user_id=user_id,
            plan_id=plan_id,
            amount=amount,
            currency=currency,
            payment_method=method,
            status="pending",
            receipt_file_id=receipt_file_id,
        )
        payment_id = await self.repo.create_payment(payment)
        logger.info(f"Created pending payment #{payment_id} for user {user_id}")
        return payment_id

    async def approve_payment(self, payment_id: int, admin_id: int) -> Optional[Payment]:
        """Mark payment as approved by administrator."""
        payment = await self.repo.get_payment(payment_id)
        if not payment or payment.status != "pending":
            return None

        await self.repo.update_payment_status(payment_id, "approved", reviewed_by=admin_id)
        payment.status = "approved"
        payment.reviewed_by = admin_id
        logger.info(f"Admin {admin_id} approved payment #{payment_id}")
        return payment

    async def reject_payment(self, payment_id: int, admin_id: int) -> Optional[Payment]:
        """Mark payment as rejected by administrator."""
        payment = await self.repo.get_payment(payment_id)
        if not payment or payment.status != "pending":
            return None

        await self.repo.update_payment_status(payment_id, "rejected", reviewed_by=admin_id)
        payment.status = "rejected"
        payment.reviewed_by = admin_id
        logger.info(f"Admin {admin_id} rejected payment #{payment_id}")
        return payment
