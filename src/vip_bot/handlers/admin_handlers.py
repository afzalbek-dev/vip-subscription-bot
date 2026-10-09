"""Admin handlers for managing subscriptions, approvals, and statistics."""

import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from vip_bot.config import Settings
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.payment_service import PaymentService
from vip_bot.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)
admin_router = Router(name="admin_router")


@admin_router.message(Command("admin"))
@admin_router.message(Command("stats"))
async def cmd_admin_stats(message: Message, repo: DatabaseRepository, settings: Settings):
    """Display administrative metrics dashboard."""
    if not settings.is_admin(message.from_user.id):
        return

    stats = await repo.get_stats()
    text = (
        f"📊 *VIP Bot Administrator Paneli*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Jami foydalanuvchilar:* `{stats['total_users']}`\n"
        f"👑 *Faol VIP a'zolar:* `{stats['active_subs']}`\n"
        f"⏳ *Kutilayotgan to'lovlar:* `{stats['pending_payments']}`\n"
        f"💰 *Jami tushum (UZS):* `{stats['total_revenue_uzs']:,} so'm`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 Yangi kvitansiyalar kelganda to'g'ridan-to'g'ri xabarnoma orqali tasdiqlash mumkin."
    )
    await message.answer(text, parse_mode="Markdown")


@admin_router.callback_query(F.data.startswith("adm_appr:"))
async def on_admin_approve_payment(
    callback: CallbackQuery,
    repo: DatabaseRepository,
    payment_service: PaymentService,
    sub_service: SubscriptionService,
    settings: Settings,
    bot: Bot,
):
    """Handle administrator payment approval."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await payment_service.approve_payment(payment_id, admin_id=callback.from_user.id)
    if not payment:
        await callback.answer("To'lov topilmadi yoki allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Grant VIP subscription & generate single-use invite link
    sub, invite_link = await sub_service.grant_subscription(bot, payment.user_id, payment.plan_id)
    plan = await repo.get_plan(payment.plan_id)
    end_str = sub.end_date.strftime("%Y-%m-%d %H:%M")

    # Notify user
    user_msg = (
        f"🎉 *Tabriklaymiz! To'lovingiz tasdiqlandi!*\n\n"
        f"👑 *Tarif:* {plan.name if plan else payment.plan_id}\n"
        f"🗓 *Amal qilish muddati:* `{end_str}` (UTC)\n\n"
        f"🔗 *VIP Kanalga bir martalik kirish havolangiz:*\n"
        f"{invite_link}\n\n"
        f"⚠️ *Eslatma:* Bu havola faqat bir marta ishlaydi va siz uchun maxsus yaratildi. Boshqalarga bermang!"
    )
    try:
        await bot.send_message(chat_id=payment.user_id, text=user_msg, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not notify user {payment.user_id}: {e}")

    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n"
            f"✅ *TASDIQLANDI* — Admin: {callback.from_user.full_name}"
        ),
        parse_mode="Markdown",
    )
    await callback.answer("To'lov tasdiqlandi va a'zolik berildi!")


@admin_router.callback_query(F.data.startswith("adm_rejc:"))
async def on_admin_reject_payment(
    callback: CallbackQuery,
    payment_service: PaymentService,
    settings: Settings,
    bot: Bot,
):
    """Handle administrator payment rejection."""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[1])
    payment = await payment_service.reject_payment(payment_id, admin_id=callback.from_user.id)
    if not payment:
        await callback.answer("To'lov topilmadi yoki allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Notify user
    try:
        await bot.send_message(
            chat_id=payment.user_id,
            text=(
                f"❌ *Hurmatli foydalanuvchi!*\n\n"
                f"Siz yuborgan #{payment_id} raqamli to'lov kvitansiyasi tasdiqlanmadi.\n"
                f"Iltimos, haqiqiy to'lov chekini qayta yuboring yoki administratorga murojaat qiling."
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"Could not send rejection to user {payment.user_id}: {e}")

    await callback.message.edit_caption(
        caption=(
            f"{callback.message.caption}\n\n"
            f"❌ *RAD ETILDI* — Admin: {callback.from_user.full_name}"
        ),
        parse_mode="Markdown",
    )
    await callback.answer("To'lov rad etildi.")
