"""Background worker to check expiring and expired subscriptions."""

import asyncio
import logging
from aiogram import Bot

from vip_bot.config import Settings
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.channel_service import ChannelService

logger = logging.getLogger(__name__)


class ExpiryWorker:
    """Monitors subscriptions for expiration alerts and automatic channel revocation."""

    def __init__(self, settings: Settings, repo: DatabaseRepository, channel_service: ChannelService):
        self.settings = settings
        self.repo = repo
        self.channel_service = channel_service
        self._running = False

    async def process_expiring_reminders(self, bot: Bot) -> int:
        """Find members expiring in next 24h and send renewal reminder."""
        subs = await self.repo.get_expiring_subscriptions(hours=self.settings.reminder_hours_before_expiry)
        sent_count = 0

        for sub in subs:
            try:
                date_str = sub.end_date.strftime("%Y-%m-%d %H:%M")
                msg = (
                    f"⏰ *VIP Obuna Eslatmasi!*\n\n"
                    f"Hurmatli foydalanuvchi, sizning VIP kanalga obunangiz muddati *{date_str}* da tugaydi.\n\n"
                    f"Kirish imkoniyatini saqlab qolish uchun hozirdan yangilang: /plans"
                )
                await bot.send_message(chat_id=sub.user_id, text=msg, parse_mode="Markdown")
                await self.repo.mark_reminder_sent(sub.id)
                sent_count += 1
                logger.info(f"Sent 24h expiry reminder to user {sub.user_id}")
            except Exception as e:
                logger.warning(f"Could not send reminder to user {sub.user_id}: {e}")

        return sent_count

    async def process_expired_revocations(self, bot: Bot) -> int:
        """Find members whose subscription expired, kick from channel, and notify."""
        subs = await self.repo.get_expired_subscriptions()
        revoked_count = 0

        for sub in subs:
            try:
                # 1. Remove from channel
                await self.channel_service.kick_expired_member(bot, sub.user_id)

                # 2. Mark in database
                await self.repo.mark_subscription_expired(sub.id)

                # 3. Inform user
                msg = (
                    "🔒 *VIP Obuna Muddati Yakunlandi!*\n\n"
                    "Sizning VIP kanalga obunangiz muddati tugadi va a'zolik bekor qilindi.\n"
                    "Qayta a'zo bo'lish uchun /plans buyrug'i orqali yangi tarif tanlashingiz mumkin."
                )
                try:
                    await bot.send_message(chat_id=sub.user_id, text=msg, parse_mode="Markdown")
                except Exception:
                    pass

                revoked_count += 1
                logger.info(f"Revoked expired VIP access for user {sub.user_id}")
            except Exception as e:
                logger.error(f"Error revoking user {sub.user_id}: {e}")

        return revoked_count

    async def run(self, bot: Bot) -> None:
        """Continuous execution loop."""
        self._running = True
        logger.info("Subscription Expiry Worker started.")
        while self._running:
            try:
                await self.process_expiring_reminders(bot)
                await self.process_expired_revocations(bot)
            except Exception as e:
                logger.error(f"Error in ExpiryWorker loop: {e}")

            await asyncio.sleep(self.settings.expiry_check_interval_seconds)

    def stop(self) -> None:
        """Signal worker to terminate."""
        self._running = False
