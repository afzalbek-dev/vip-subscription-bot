"""Subscription management and access provisioning service."""

import logging
from typing import Optional, Tuple
from aiogram import Bot

from vip_bot.database.models import Subscription, Plan
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.channel_service import ChannelService

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Orchestrates granting and verifying user VIP channel access."""

    def __init__(self, repo: DatabaseRepository, channel_service: ChannelService):
        self.repo = repo
        self.channel_service = channel_service

    async def grant_subscription(
        self, bot: Bot, user_id: int, plan_id: str
    ) -> Tuple[Subscription, Optional[str]]:
        """Grant or extend subscription and produce a single-use channel invite link."""
        plan = await self.repo.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        sub = await self.repo.create_or_extend_subscription(
            user_id=user_id, plan_id=plan_id, duration_days=plan.duration_days
        )

        invite_link = await self.channel_service.create_one_time_invite_link(bot, user_id)
        logger.info(f"Subscription granted for user {user_id} until {sub.end_date.strftime('%Y-%m-%d')}")
        return sub, invite_link

    async def check_user_status(self, user_id: int) -> Optional[Subscription]:
        """Check if user has an active VIP membership."""
        return await self.repo.get_active_subscription(user_id)
