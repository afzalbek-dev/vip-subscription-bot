"""User command and callback handlers for VIP Subscription Bot."""

import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from vip_bot.config import Settings
from vip_bot.database.models import User
from vip_bot.database.repository import DatabaseRepository
from vip_bot.services.payment_service import PaymentService

logger = logging.getLogger(__name__)
user_router = Router(name="user_router")


class PaymentStates(StatesGroup):
    waiting_for_receipt = State()


@user_router.message(CommandStart())
async def cmd_start(message: Message, repo: DatabaseRepository):
    """Handle /start command and register user."""
    user = User(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or "Foydalanuvchi",
    )
    await repo.upsert_user(user)

    text = (
        f"👋 Salom, *{user.full_name}*!\n\n"
        f"👑 *VIP Kanal A'zolik Botiga xush kelibsiz!*\n\n"
        f"Bu yerda siz yopiq premium kanalga obuna xarid qilishingiz, "
        f"to'lovlarni tekshirtirishingiz va a'zolik holatingizni nazorat qilishingiz mumkin.\n\n"
        f"📌 *Mavjud buyruqlar:*\n"
        f"• /plans — VIP tariflar va narxlar\n"
        f"• /status — Obuna holatingizni tekshirish\n"
        f"• /help — Yordam va ma'lumot"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 VIP Tariflarni Ko'rish", callback_data="show_plans")],
        [InlineKeyboardButton(text="📊 Obuna Holatim", callback_data="check_status")],
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@user_router.message(Command("plans"))
@user_router.callback_query(F.data == "show_plans")
async def cmd_plans(event: Message | CallbackQuery, repo: DatabaseRepository):
    """Display active subscription tiers."""
    plans = await repo.get_plans(only_active=True)
    if not plans:
        text = "Hozircha faol tariflar mavjud emas."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text)
        else:
            await event.answer(text)
        return

    text = "💎 *Mavjud VIP Tariflar:*\n\n"
    buttons = []
    for p in plans:
        text += f"• *{p.name}* — `{p.price_uzs:,} so'm` (${p.price_usd})\n  _{p.description}_\n\n"
        buttons.append([InlineKeyboardButton(text=f"Tanlash: {p.name}", callback_data=f"plan:{p.id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@user_router.callback_query(F.data.startswith("plan:"))
async def on_plan_selected(callback: CallbackQuery, repo: DatabaseRepository):
    """Show payment methods for selected plan."""
    plan_id = callback.data.split("plan:")[1]
    plan = await repo.get_plan(plan_id)
    if not plan:
        await callback.answer("Tarif topilmadi!", show_alert=True)
        return

    text = (
        f"Tanlangan tarif: *{plan.name}*\n"
        f"Narxi: `{plan.price_uzs:,} so'm` (${plan.price_usd})\n\n"
        f"To'lov turini tanlang:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme / Uzcard", callback_data=f"pay:{plan.id}:payme")],
        [InlineKeyboardButton(text="💳 Click / Humo", callback_data=f"pay:{plan.id}:click")],
        [InlineKeyboardButton(text="💎 USDT (TRC-20)", callback_data=f"pay:{plan.id}:crypto")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="show_plans")],
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@user_router.callback_query(F.data.startswith("pay:"))
async def on_pay_method_selected(
    callback: CallbackQuery, repo: DatabaseRepository, payment_service: PaymentService, state: FSMContext
):
    """Provide payment requisites and await receipt."""
    parts = callback.data.split(":")
    plan_id = parts[1]
    method = parts[2]

    plan = await repo.get_plan(plan_id)
    if not plan:
        await callback.answer("Tarif topilmadi!", show_alert=True)
        return

    instructions = payment_service.get_payment_details_text(plan, method)
    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(plan_id=plan_id, method=method)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")]
    ])
    await callback.message.edit_text(instructions, parse_mode="Markdown", reply_markup=keyboard)


@user_router.callback_query(F.data == "cancel_payment")
async def on_cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Cancel payment flow."""
    await state.clear()
    await callback.message.edit_text("To'lov bekor qilindi. Bosh menyu: /start")


@user_router.message(PaymentStates.waiting_for_receipt, F.photo)
async def on_receipt_photo_received(
    message: Message,
    state: FSMContext,
    payment_service: PaymentService,
    repo: DatabaseRepository,
    settings: Settings,
    bot: Bot,
):
    """Receive receipt photo, save payment, and notify admins."""
    data = await state.get_data()
    plan_id = data.get("plan_id")
    method = data.get("method")
    photo = message.photo[-1]  # Highest resolution photo

    payment_id = await payment_service.register_payment_submission(
        user_id=message.from_user.id,
        plan_id=plan_id,
        method=method,
        receipt_file_id=photo.file_id,
    )
    await state.clear()

    plan = await repo.get_plan(plan_id)
    await message.answer(
        f"✅ *Chek qabul qilindi!* (To'lov #{payment_id})\n\n"
        f"Administrator tekshiruvidan so'ng sizga VIP kanal taklif havolasi yuboriladi.\n"
        f"Iltimos, kuting.",
        parse_mode="Markdown",
    )

    # Notify administrators
    admin_text = (
        f"🔔 *Yangi VIP To'lov Kvitansiyasi!* (#{payment_id})\n\n"
        f"👤 *Foydalanuvchi:* {message.from_user.full_name} (`{message.from_user.id}`)\n"
        f"🏷 *Username:* @{message.from_user.username or 'yo_q'}\n"
        f"📦 *Tarif:* {plan.name if plan else plan_id}\n"
        f"💳 *Usul:* {method.upper()}\n"
    )
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_appr:{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rejc:{payment_id}"),
        ]
    ])

    for admin_id in settings.admin_ids:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard,
            )
        except Exception as e:
            logger.warning(f"Could not alert admin {admin_id}: {e}")


@user_router.message(Command("status"))
@user_router.callback_query(F.data == "check_status")
async def cmd_status(event: Message | CallbackQuery, repo: DatabaseRepository):
    """Check user's current subscription status."""
    user_id = event.from_user.id
    sub = await repo.get_active_subscription(user_id)

    if not sub:
        text = (
            "❌ Sizda hozirda faol VIP obuna mavjud emas.\n\n"
            "Tariflar bilan tanishish uchun /plans buyrug'idan foydalaning."
        )
    else:
        plan = await repo.get_plan(sub.plan_id)
        plan_name = plan.name if plan else sub.plan_id
        end_str = sub.end_date.strftime("%Y-%m-%d %H:%M")
        text = (
            f"👑 *Sizning VIP A'zoligingiz Faol!*\n\n"
            f"📦 *Tarif:* {plan_name}\n"
            f"🗓 *Tugash sanasi:* `{end_str}` (UTC)\n"
            f"✅ Barcha premium imtiyozlar faollashtirilgan."
        )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown")
