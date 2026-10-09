"""Tests for ChannelService."""

import pytest
from vip_bot.services.channel_service import ChannelService


@pytest.mark.asyncio
async def test_create_invite_link(mock_bot):
    """Verify single-use invite link creation via Bot API."""
    service = ChannelService(channel_id=-1001234567890)
    link = await service.create_one_time_invite_link(mock_bot, user_id=444)

    assert link == "https://t.me/+test_one_time_link"
    mock_bot.create_chat_invite_link.assert_awaited_once_with(
        chat_id=-1001234567890,
        name="VIP_Member_444",
        member_limit=1,
    )


@pytest.mark.asyncio
async def test_kick_expired_member(mock_bot):
    """Verify kick procedure (ban and unban)."""
    service = ChannelService(channel_id=-1001234567890)
    success = await service.kick_expired_member(mock_bot, user_id=777)

    assert success is True
    mock_bot.ban_chat_member.assert_awaited_once_with(chat_id=-1001234567890, user_id=777)
    mock_bot.unban_chat_member.assert_awaited_once_with(chat_id=-1001234567890, user_id=777)
