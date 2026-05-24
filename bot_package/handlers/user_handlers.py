from telegram import Update, constants
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import async_session
from ..models import Purchase, Transaction, User
from ..services.inventory_service import InventoryService
from ..services.price_service import PriceService
from ..utils.keyboards import back_to_main, buy_volume_keyboard, main_menu_keyboard, wallet_keyboard
from ..utils.messages import (
    BUY_MENU_TEXT,
    HELP_TEXT,
    MAIN_MENU_TEXT,
    NO_PURCHASE,
    PURCHASE_SUCCESS,
    WALLET_TEXT,
)


async def get_or_create_user(telegram_id: int, name: str, username: str | None):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, first_name=name, username=username)
            session.add(user)
            await session.commit()
        return user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await get_or_create_user(user.id, user.first_name, user.username)
    await update.message.reply_text(
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def buy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        prices = await PriceService.get_all_prices(session)

    await query.edit_message_text(
        BUY_MENU_TEXT,
        reply_markup=buy_volume_keyboard(prices),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = await get_or_create_user(query.from_user.id, query.from_user.first_name, query.from_user.username)
    await query.answer()
    await query.edit_message_text(
        WALLET_TEXT.format(f"{user.wallet_balance:,}"),
        reply_markup=wallet_keyboard(),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def process_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await get_or_create_user(query.from_user.id, query.from_user.first_name, query.from_user.username)
    volume = int(query.data.split("_")[1])

    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.telegram_id == query.from_user.id))
        db_user = user_result.scalar_one()

        if db_user.is_blocked:
            await query.answer("Your account is blocked.", show_alert=True)
            return

        price = await PriceService.get_price(session, volume)
        if not price:
            await query.answer("This plan is not available.", show_alert=True)
            return

        if db_user.wallet_balance < price:
            await query.answer(f"Insufficient balance. Required: {price:,}", show_alert=True)
            return

        config = await InventoryService.get_available_config(session, volume)
        if not config:
            await query.answer(f"The {volume}GB plan is out of stock.", show_alert=True)
            return

        db_user.wallet_balance -= price
        sold = await InventoryService.sell_config(session, config, db_user.telegram_id)
        if not sold:
            await session.rollback()
            await query.answer(f"The {volume}GB plan is out of stock.", show_alert=True)
            return

        purchase = Purchase(
            user_id=db_user.telegram_id,
            config_id=config.id,
            volume_gb=volume,
            price=price,
        )
        session.add(purchase)

        transaction = Transaction(
            user_id=db_user.telegram_id,
            amount=-price,
            type="purchase",
            description=f"Purchase {volume}GB",
        )
        session.add(transaction)
        await session.commit()

        await query.answer("Purchase complete.", show_alert=True)
        await query.edit_message_text(
            PURCHASE_SUCCESS.format(volume, f"{price:,}", config.sub_link),
            reply_markup=back_to_main(),
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )


async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        HELP_TEXT,
        reply_markup=back_to_main(),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        stmt = (
            select(Purchase)
            .options(selectinload(Purchase.config))
            .where(Purchase.user_id == query.from_user.id)
            .order_by(Purchase.purchased_at.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        purchases = result.scalars().all()

    if not purchases:
        await query.edit_message_text(NO_PURCHASE, reply_markup=back_to_main())
        return

    text = "Your latest purchases\n\n"
    for purchase in purchases:
        text += (
            f"{purchase.volume_gb}GB | {purchase.price:,}\n"
            f"{purchase.purchased_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"`{purchase.config.sub_link}`\n\n"
        )

    await query.edit_message_text(
        text,
        reply_markup=back_to_main(),
        parse_mode=constants.ParseMode.MARKDOWN_V2,
    )


user_handlers = [
    CommandHandler("start", start),
    CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
    CallbackQueryHandler(buy_menu, pattern="^buy_menu$"),
    CallbackQueryHandler(wallet_menu, pattern="^wallet_menu$"),
    CallbackQueryHandler(history_menu, pattern="^history_menu$"),
    CallbackQueryHandler(process_purchase, pattern="^buy_"),
    CallbackQueryHandler(help_menu, pattern="^help_menu$"),
]
