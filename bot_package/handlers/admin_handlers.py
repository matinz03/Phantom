from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..auth import AuthManager
from ..config_loader import BotConfig
from ..database import async_session
from ..models import Purchase
from ..services.inventory_service import InventoryService
from ..services.admin_service import ALL_PERMISSIONS, AdminService, normalize_permissions
from ..services.price_service import PriceService
from ..services.user_service import UserService
from ..utils.keyboards import (
    admin_inventory_keyboard,
    admin_main_keyboard,
    admin_management_keyboard,
    admin_prices_keyboard,
    admin_reports_keyboard,
    admin_users_keyboard,
    volume_selection_keyboard,
)
from ..utils.messages import (
    ADD_CONFIG_VOLUME,
    ADMIN_MAIN_MENU,
    AUTH_ENTER_PASSWORD,
    AUTH_EXPIRED,
    AUTH_FAILED,
    AUTH_SUCCESS,
    CHARGE_AMOUNT_PROMPT,
    CHARGE_SUCCESS,
    CHARGE_WALLET_PROMPT,
    EDIT_PRICE_PROMPT,
    LINKS_DETECTED,
    NO_LINKS_FOUND,
    PRICE_LIST_HEADER,
    PRICE_UPDATED,
    SEARCH_USER_PROMPT,
    SEND_LINKS_PROMPT,
    STOCK_STATUS_HEADER,
)
from ..utils.validators import extract_links_from_text


(CHOOSE_VOLUME_ADD, COLLECT_LINKS, CHOOSE_VOLUME_PRICE, ENTER_NEW_PRICE, SEARCH_USER, CHARGE_USER_ID, CHARGE_AMOUNT) = range(7)


def require_auth(func=None, *, permission: str | None = None, owner_only: bool = False):
    def decorator(handler_func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            async with async_session() as session:
                if owner_only:
                    is_allowed = await AdminService.is_owner(session, update.effective_user.id)
                else:
                    is_allowed = await AdminService.can_access(session, update.effective_user.id, permission)

            if not is_allowed:
                await update.effective_message.reply_text("Access denied.")
                return ConversationHandler.END

            if not AuthManager.is_authenticated(update.effective_user.id):
                context.user_data["awaiting_password"] = True
                await update.effective_message.reply_text(AUTH_EXPIRED)
                return ConversationHandler.END

            AuthManager.refresh_session(update.effective_user.id)
            return await handler_func(update, context)

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


async def is_known_admin(user_id: int) -> bool:
    async with async_session() as session:
        return await AdminService.can_access(session, user_id)


async def is_owner(user_id: int) -> bool:
    async with async_session() as session:
        return await AdminService.is_owner(session, user_id)


async def require_owner_message(update: Update) -> bool:
    if not await is_owner(update.effective_user.id):
        await update.effective_message.reply_text("Access denied. Owner permissions are required.")
        return False
    if not AuthManager.is_authenticated(update.effective_user.id):
        await update.effective_message.reply_text(AUTH_EXPIRED)
        return False
    return True


async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_known_admin(update.effective_user.id):
        if not BotConfig.is_admin(update.effective_user.id):
            await update.effective_message.reply_text("Access denied.")
            return
        async with async_session() as session:
            await AdminService.sync_configured_admins(session)

    if AuthManager.is_authenticated(update.effective_user.id):
        await update.message.reply_text(
            ADMIN_MAIN_MENU.format(update.effective_user.first_name),
            reply_markup=admin_main_keyboard(),
        )
        return

    context.user_data["awaiting_password"] = True
    await update.message.reply_text(AUTH_ENTER_PASSWORD)


async def check_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_known_admin(update.effective_user.id):
        return
    if not context.user_data.get("awaiting_password"):
        return

    password = update.message.text
    try:
        await update.message.delete()
    except Exception:
        pass

    if password == BotConfig.ADMIN_PASSWORD:
        AuthManager.authenticate(update.effective_user.id)
        context.user_data["awaiting_password"] = False
        success_msg = await update.message.reply_text(AUTH_SUCCESS)
        context.job_queue.run_once(delete_later, 3, data=success_msg)
        await update.message.reply_text(
            ADMIN_MAIN_MENU.format(update.effective_user.first_name),
            reply_markup=admin_main_keyboard(),
        )
        return

    fail_msg = await update.message.reply_text(AUTH_FAILED)
    context.job_queue.run_once(delete_later, 5, data=fail_msg)


async def delete_later(context: ContextTypes.DEFAULT_TYPE):
    message = context.job.data
    try:
        await message.delete()
    except Exception:
        pass


@require_auth
async def admin_menu_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    nav_map = {
        "admin_main": (ADMIN_MAIN_MENU.format(query.from_user.first_name), admin_main_keyboard()),
        "admin_inventory_menu": ("Inventory management", admin_inventory_keyboard()),
        "admin_prices_menu": ("Price management", admin_prices_keyboard()),
        "admin_users_menu": ("User management", admin_users_keyboard()),
        "admin_reports_menu": ("Sales reports", admin_reports_keyboard()),
    }

    text, keyboard = nav_map[query.data]
    await query.edit_message_text(text, reply_markup=keyboard)


@require_auth(owner_only=True)
async def admin_management_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Admin management\n\n"
        "Commands:\n"
        "/admins\n"
        "/addadmin <telegram_id> <permissions>\n"
        "/removeadmin <telegram_id>\n"
        "/setadminperms <telegram_id> <permissions>\n\n"
        f"Permissions: {', '.join(ALL_PERMISSIONS)} or all",
        reply_markup=admin_management_keyboard(),
    )


@require_auth
async def admin_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    AuthManager.logout(query.from_user.id)
    await query.edit_message_text("Logged out. Send /start to log in again.")


@require_auth(permission="inventory")
async def add_config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(ADD_CONFIG_VOLUME, reply_markup=volume_selection_keyboard("add_vol"))
    return CHOOSE_VOLUME_ADD


@require_auth(permission="inventory")
async def add_config_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["adding_volume"] = int(query.data.split("_")[2])
    context.user_data["collected_links"] = []
    await query.edit_message_text(SEND_LINKS_PROMPT)
    return COLLECT_LINKS


@require_auth(permission="inventory")
async def collect_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_links = extract_links_from_text(update.message.text)
    if new_links:
        context.user_data.setdefault("collected_links", []).extend(new_links)
        await update.message.reply_text(LINKS_DETECTED.format(len(new_links), len(context.user_data["collected_links"])))
    else:
        await update.message.reply_text(NO_LINKS_FOUND)
    return COLLECT_LINKS


@require_auth(permission="inventory")
async def done_collecting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume = context.user_data.get("adding_volume")
    links = context.user_data.get("collected_links", [])
    if not volume or not links:
        await update.message.reply_text("No links were collected.", reply_markup=admin_inventory_keyboard())
        return ConversationHandler.END

    async with async_session() as session:
        count = await InventoryService.add_configs(session, volume, links)

    await update.message.reply_text(
        f"Added {count} config links for {volume}GB.",
        reply_markup=admin_inventory_keyboard(),
    )
    return ConversationHandler.END


@require_auth(permission="inventory")
async def stock_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        stock = await InventoryService.get_stock_status(session)

    message = STOCK_STATUS_HEADER
    for volume, count in stock.items():
        if count < 5:
            status = "critical"
        elif count <= 10:
            status = "medium"
        else:
            status = "healthy"
        message += f"{volume}GB: {count} ({status})\n"

    await query.edit_message_text(message, reply_markup=admin_inventory_keyboard())


@require_auth(permission="prices")
async def view_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        prices = await PriceService.get_all_prices(session)

    message = PRICE_LIST_HEADER.format(datetime.now().strftime("%Y-%m-%d %H:%M"))
    for volume, price in prices.items():
        message += f"{volume}GB: {price:,} toman\n"

    await query.edit_message_text(message, reply_markup=admin_prices_keyboard())


@require_auth(permission="prices")
async def edit_price_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Choose the volume to edit:", reply_markup=volume_selection_keyboard("edit_price"))
    return CHOOSE_VOLUME_PRICE


@require_auth(permission="prices")
async def edit_price_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    volume = int(query.data.split("_")[2])
    context.user_data["editing_volume"] = volume

    async with async_session() as session:
        current_price = await PriceService.get_price(session, volume)

    await query.edit_message_text(EDIT_PRICE_PROMPT.format(volume, f"{current_price:,}"))
    return ENTER_NEW_PRICE


@require_auth(permission="prices")
async def save_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume = context.user_data.get("editing_volume")
    try:
        new_price = int(update.message.text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("Enter a valid numeric price.")
        return ENTER_NEW_PRICE

    if new_price <= 0:
        await update.message.reply_text("Price must be greater than zero.")
        return ENTER_NEW_PRICE

    async with async_session() as session:
        success = await PriceService.update_price(session, volume, new_price)

    if success:
        await update.message.reply_text(
            PRICE_UPDATED.format(volume, f"{new_price:,}", datetime.now().strftime("%H:%M:%S")),
            reply_markup=admin_prices_keyboard(),
        )
    else:
        await update.message.reply_text("Could not update price.", reply_markup=admin_prices_keyboard())

    return ConversationHandler.END


@require_auth(permission="users")
async def search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(SEARCH_USER_PROMPT)
    return SEARCH_USER


@require_auth(permission="users")
async def search_user_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    async with async_session() as session:
        user = await UserService.search_user(session, query_text)

    if user:
        status = "blocked" if user.is_blocked else "active"
        message = (
            "User information\n\n"
            f"ID: {user.telegram_id}\n"
            f"Name: {user.first_name}\n"
            f"Username: @{user.username or 'none'}\n"
            f"Wallet: {user.wallet_balance:,} toman\n"
            f"Joined: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"Status: {status}"
        )
        await update.message.reply_text(message, reply_markup=admin_users_keyboard())
    else:
        await update.message.reply_text("User not found.", reply_markup=admin_users_keyboard())

    return ConversationHandler.END


@require_auth(permission="users")
async def charge_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(CHARGE_WALLET_PROMPT)
    return CHARGE_USER_ID


@require_auth(permission="users")
async def charge_wallet_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["charge_user_id"] = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("Enter a valid numeric Telegram user ID.")
        return CHARGE_USER_ID

    await update.message.reply_text(CHARGE_AMOUNT_PROMPT)
    return CHARGE_AMOUNT


@require_auth(permission="users")
async def charge_wallet_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("charge_user_id")
    try:
        amount = int(update.message.text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("Enter a valid numeric amount.")
        return CHARGE_AMOUNT

    if amount <= 0:
        await update.message.reply_text("Charge amount must be greater than zero.")
        return CHARGE_AMOUNT

    async with async_session() as session:
        success = await UserService.charge_wallet(session, user_id, amount, update.effective_user.id)

    if success:
        await update.message.reply_text(
            CHARGE_SUCCESS.format(user_id, f"{amount:,}", datetime.now().strftime("%H:%M:%S")),
            reply_markup=admin_users_keyboard(),
        )
    else:
        await update.message.reply_text("User not found.", reply_markup=admin_users_keyboard())

    return ConversationHandler.END


@require_auth(permission="reports")
async def sales_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    days = int(query.data.split("_")[1])
    period_names = {1: "today", 7: "this week", 30: "this month"}
    since = datetime.now(timezone.utc) - timedelta(days=days)

    async with async_session() as session:
        result = await session.execute(select(Purchase).where(Purchase.purchased_at >= since))
        purchases = result.scalars().all()

    total_revenue = sum(purchase.price for purchase in purchases)
    volume_stats = {}
    for purchase in purchases:
        volume_stats[purchase.volume_gb] = volume_stats.get(purchase.volume_gb, 0) + 1

    message = f"Sales report for {period_names.get(days, f'{days} days')}\n\n"
    message += f"Sales count: {len(purchases)}\n"
    message += f"Total revenue: {total_revenue:,} toman\n\n"
    if volume_stats:
        message += "By volume:\n"
        for volume, count in sorted(volume_stats.items()):
            message += f"{volume}GB: {count}\n"

    await query.edit_message_text(message, reply_markup=admin_reports_keyboard())


@require_auth(permission="users")
async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        stats = await UserService.get_user_stats(session)

    message = (
        "User stats\n\n"
        f"Total users: {stats['total_users']}\n"
        f"New today: {stats['new_today']}\n"
        f"Total wallet balance: {stats['total_balance']:,} toman\n"
    )

    await query.edit_message_text(message, reply_markup=admin_users_keyboard())


@require_auth(owner_only=True)
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with async_session() as session:
        admins = await AdminService.list_admins(session)

    lines = ["Active admins\n"]
    for admin in admins:
        role = "owner" if admin.is_owner else "admin"
        permissions = "all" if admin.is_owner else admin.permissions
        lines.append(f"{admin.telegram_id} | {role} | {permissions}")

    await update.effective_message.reply_text("\n".join(lines))


@require_auth(owner_only=True)
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text(
            f"Usage: /addadmin <telegram_id> <permissions>\nPermissions: {', '.join(ALL_PERMISSIONS)} or all"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Telegram ID must be numeric.")
        return

    permissions = normalize_permissions(context.args[1:] or "reports")
    if not permissions:
        await update.effective_message.reply_text(
            f"Provide at least one valid permission: {', '.join(ALL_PERMISSIONS)} or all"
        )
        return

    async with async_session() as session:
        admin = await AdminService.add_or_update_admin(
            session,
            telegram_id=telegram_id,
            permissions=permissions,
            created_by=update.effective_user.id,
            is_owner=False,
        )
        await session.commit()

    await update.effective_message.reply_text(f"Admin {admin.telegram_id} saved with permissions: {admin.permissions}")


@require_auth(owner_only=True)
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /removeadmin <telegram_id>")
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Telegram ID must be numeric.")
        return

    if telegram_id == update.effective_user.id:
        await update.effective_message.reply_text("Owners cannot remove themselves.")
        return

    async with async_session() as session:
        removed = await AdminService.remove_admin(session, telegram_id)
        await session.commit()

    if removed:
        await update.effective_message.reply_text(f"Admin {telegram_id} removed.")
    else:
        await update.effective_message.reply_text("Admin was not found or is an owner.")


@require_auth(owner_only=True)
async def set_admin_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            f"Usage: /setadminperms <telegram_id> <permissions>\nPermissions: {', '.join(ALL_PERMISSIONS)} or all"
        )
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.effective_message.reply_text("Telegram ID must be numeric.")
        return

    permissions = normalize_permissions(context.args[1:])
    if not permissions:
        await update.effective_message.reply_text(
            f"Provide at least one valid permission: {', '.join(ALL_PERMISSIONS)} or all"
        )
        return

    async with async_session() as session:
        admin = await AdminService.get_admin(session, telegram_id)
        if not admin:
            await update.effective_message.reply_text("Admin not found.")
            return
        if admin.is_owner:
            await update.effective_message.reply_text("Owner permissions cannot be changed.")
            return
        admin.permissions = permissions
        admin.updated_at = datetime.now(timezone.utc)
        await session.commit()

    await update.effective_message.reply_text(f"Admin {telegram_id} permissions updated: {permissions}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.", reply_markup=admin_main_keyboard())
    return ConversationHandler.END


add_config_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_config_start, pattern="^admin_add_config$")],
    states={
        CHOOSE_VOLUME_ADD: [CallbackQueryHandler(add_config_volume, pattern="^add_vol_")],
        COLLECT_LINKS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_links),
            CommandHandler("done", done_collecting),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

edit_price_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_price_select, pattern="^admin_edit_price_select$")],
    states={
        CHOOSE_VOLUME_PRICE: [CallbackQueryHandler(edit_price_enter, pattern="^edit_price_")],
        ENTER_NEW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_price)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

search_user_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(search_user_start, pattern="^admin_search_user$")],
    states={SEARCH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_user_result)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

charge_wallet_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(charge_wallet_start, pattern="^admin_charge_wallet$")],
    states={
        CHARGE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, charge_wallet_user)],
        CHARGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, charge_wallet_execute)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

admin_handlers = [
    CommandHandler("start", admin_start),
    CommandHandler("admins", list_admins),
    CommandHandler("addadmin", add_admin),
    CommandHandler("removeadmin", remove_admin),
    CommandHandler("setadminperms", set_admin_permissions),
    CallbackQueryHandler(admin_logout, pattern="^admin_logout$"),
    CallbackQueryHandler(admin_management_menu, pattern="^admin_admins_menu$"),
    CallbackQueryHandler(admin_menu_navigation, pattern="^(admin_main|admin_inventory_menu|admin_prices_menu|admin_users_menu|admin_reports_menu)$"),
    CallbackQueryHandler(stock_status, pattern="^admin_stock_status$"),
    CallbackQueryHandler(view_prices, pattern="^admin_view_prices$"),
    CallbackQueryHandler(sales_report, pattern="^report_"),
    CallbackQueryHandler(user_stats, pattern="^admin_user_stats$"),
    add_config_conv,
    edit_price_conv,
    search_user_conv,
    charge_wallet_conv,
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_admin_password),
]
