"""Main application entry point for VIP Subscription Bot."""

import asyncio
import logging
import sys

from vip_bot.config import get_settings
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.channel_service import ChannelService
from vip_bot.services.payment_service import PaymentService
from vip_bot.services.subscription_service import SubscriptionService
from vip_bot.workers.expiry_worker import ExpiryWorker
from vip_bot.bot import create_bot, create_dispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("vip_bot")


async def main():
    """Start bot services, background worker, and polling."""
    settings = get_settings()
    logger.info("Initializing VIP Subscription Bot...")

    # Database
    repo = DatabaseRepository(settings.sqlite_path)
    await repo.init_db()

    # Services
    channel_service = ChannelService(settings.vip_channel_id)
    payment_service = PaymentService(settings, repo)
    sub_service = SubscriptionService(repo, channel_service)

    # Bot & Dispatcher
    bot = create_bot(settings)
    dp = create_dispatcher(settings, repo, channel_service, payment_service, sub_service)

    # Background worker
    worker = ExpiryWorker(settings, repo, channel_service)
    worker_task = asyncio.create_task(worker.run(bot))

    logger.info("Starting bot polling and worker task...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        worker.stop()
        worker_task.cancel()
        await bot.session.close()
        logger.info("VIP Subscription Bot gracefully stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot exited.")
