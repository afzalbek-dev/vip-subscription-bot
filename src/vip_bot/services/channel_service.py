"""Telegram Channel access management service."""

import logging
from typing import Optional
from aiogram import Bot

logger = logging.getLogger(__name__)


class ChannelService:
    """Manages private VIP channel invitations and membership revocation."""

    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    async def create_one_time_invite_link(self, bot: Bot, user_id: int) -> Optional[str]:
        """Generate a secure, single-use revocable invite link for approved user."""
        if not self.channel_id:
            logger.warning("VIP_CHANNEL_ID is not configured. Returning simulation link.")
            return f"https://t.me/+simulation_invite_{user_id}"

        try:
            link = await bot.create_chat_invite_link(
                chat_id=self.channel_id,
                name=f"VIP_Member_{user_id}",
                member_limit=1,
            )
            logger.info(f"Generated 1-time invite link for user {user_id}")
            return link.invite_link
        except Exception as e:
            logger.error(f"Failed to generate invite link for user {user_id}: {e}")
            return None

    async def kick_expired_member(self, bot: Bot, user_id: int) -> bool:
        """Remove expired member from the private channel (ban + immediate unban)."""
        if not self.channel_id:
            logger.info(f"[SIMULATION] Kicked user {user_id} from private channel.")
            return True

        try:
            await bot.ban_chat_member(chat_id=self.channel_id, user_id=user_id)
            await bot.unban_chat_member(chat_id=self.channel_id, user_id=user_id)
            logger.info(f"Successfully revoked VIP channel access for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to kick expired user {user_id}: {e}")
            return False
