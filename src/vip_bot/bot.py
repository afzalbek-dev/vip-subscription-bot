"""Bot and Dispatcher initialization module."""

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from vip_bot.config import Settings
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.channel_service import ChannelService
from vip_bot.services.payment_service import PaymentService
from vip_bot.services.subscription_service import SubscriptionService
from vip_bot.handlers.user_handlers import user_router
from vip_bot.handlers.admin_handlers import admin_router


def create_bot(settings: Settings) -> Bot:
    """Create and configure Aiogram Bot instance."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(
    settings: Settings,
    repo: DatabaseRepository,
    channel_service: ChannelService,
    payment_service: PaymentService,
    sub_service: SubscriptionService,
) -> Dispatcher:
    """Create and configure Dispatcher with dependency injection."""
    dp = Dispatcher()

    # Dependency injection into handlers
    dp["settings"] = settings
    dp["repo"] = repo
    dp["channel_service"] = channel_service
    dp["payment_service"] = payment_service
    dp["sub_service"] = sub_service

    # Register routers
    dp.include_router(user_router)
    dp.include_router(admin_router)

    return dp
