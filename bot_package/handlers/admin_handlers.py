from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from ..database import async_session
from ..models import Config
from ..config_loader import BotConfig
from ..auth import AuthManager
from ..utils.keyboards import *
from ..utils.messages import *
from ..utils.validators import extract_links_from_text
from ..services.inventory_service import InventoryService
from ..services.price_service import PriceService
from ..services.user_service import UserService
from ..handlers.auth_handlers import require_password, check_password, ENTER_PASSWORD
from datetime import datetime, timezone

# state های کانورسیشن
(CHOOSE_VOLUME_ADD, COLLECT_LINKS,
 CHOOSE_VOLUME_PRICE, ENTER_NEW_PRICE,
 SEARCH_USER, CHARGE_USER_ID, CHARGE_AMOUNT) = range(7)

# ============== دکوراتور احراز هویت ==============
def require_auth(func):
    """دکوراتور برای بررسی احراز هویت قبل از اجرای هر عملیات"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not AuthManager.is_authenticated(update.effective_user.id):
            await update.effective_message.reply_text(AUTH_EXPIRED)
            return await require_password(update, context)
        AuthManager.refresh_session(update.effective_user.id)
        return await func(update, context)
    return wrapper

# ============== منوی اصلی ==============
async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BotConfig.ADMIN_USER_ID:
        await update.message.reply_text("⛔️ شما دسترسی ندارید.")
        return
    
    if AuthManager.is_authenticated(update.effective_user.id):
        await update.message.reply_text(
            ADMIN_MAIN_MENU.format(update.effective_user.first_name),
            reply_markup=admin_main_keyboard()
        )
    else:
        await update.message.reply_text(AUTH_ENTER_PASSWORD)
        context.user_data['awaiting_password'] = True

async def check_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بررسی رمز ادمین (برای ورود اولیه)"""
    if not context.user_data.get('awaiting_password'):
        return
    
    password = update.message.text
    
    # حذف پیام رمز
    try:
        await update.message.delete()
    except:
        pass
    
    if password == BotConfig.ADMIN_PASSWORD:
        AuthManager.authenticate(update.effective_user.id)
        context.user_data['awaiting_password'] = False
        
        success_msg = await update.message.reply_text(AUTH_SUCCESS)
        context.job_queue.run_once(lambda ctx: success_msg.delete(), 3)
        
        await update.message.reply_text(
            ADMIN_MAIN_MENU.format(update.effective_user.first_name),
            reply_markup=admin_main_keyboard()
        )
    else:
        fail_msg = await update.message.reply_text(AUTH_FAILED)
        context.job_queue.run_once(lambda ctx: fail_msg.delete(), 5)

# ============== نویگیشن منوها ==============
@require_auth
async def admin_menu_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    nav_map = {
        "admin_main": (ADMIN_MAIN_MENU.format(query.from_user.first_name), admin_main_keyboard()),
        "admin_inventory_menu": ("📦 مدیریت انبار", admin_inventory_keyboard()),
        "admin_prices_menu": ("💰 مدیریت قیمت‌ها", admin_prices_keyboard()),
        "admin_users_menu": ("👥 مدیریت کاربران", admin_users_keyboard()),
        "admin_reports_menu": ("📊 گزارشات فروش", admin_reports_keyboard()),
    }
    
    if data in nav_map:
        text, keyboard = nav_map[data]
        await query.edit_message_text(text, reply_markup=keyboard)

@require_auth
async def admin_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    AuthManager.logout(query.from_user.id)
    await query.edit_message_text("🚪 از پنل مدیریت خارج شدید. /start برای ورود مجدد")

# ============== مدیریت انبار ==============
@require_auth
async def add_config_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(ADD_CONFIG_VOLUME, reply_markup=volume_selection_keyboard("add_vol"))
    return CHOOSE_VOLUME_ADD

@require_auth
async def add_config_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    volume = int(query.data.split("_")[2])
    context.user_data['adding_volume'] = volume
    context.user_data['collected_links'] = []
    await query.edit_message_text(SEND_LINKS_PROMPT)
    return COLLECT_LINKS

@require_auth
async def collect_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    new_links = extract_links_from_text(text)
    
    if new_links:
        context.user_data['collected_links'].extend(new_links)
        await update.message.reply_text(
            LINKS_DETECTED.format(len(new_links), len(context.user_data['collected_links']))
        )
    else:
        await update.message.reply_text(NO_LINKS_FOUND)
    
    return COLLECT_LINKS

@require_auth
async def done_collecting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume = context.user_data.get('adding_volume')
    links = context.user_data.get('collected_links', [])
    
    if not links:
        await update.message.reply_text("❌ هیچ لینکی جمع نشد!", reply_markup=admin_inventory_keyboard())
        return ConversationHandler.END
    
    async with async_session() as session:
        count = await InventoryService.add_configs(session, volume, links)
    
    await update.message.reply_text(
        f"🎉 **{count}** کانفیگ {volume}GB به انبار اضافه شد!",
        reply_markup=admin_inventory_keyboard()
    )
    return ConversationHandler.END

# ============== موجودی انبار ==============
@require_auth
async def stock_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with async_session() as session:
        stock = await InventoryService.get_stock_status(session)
    
    volume_emojis = {1: "🟢", 2: "🔵", 3: "🟣", 5: "🟠", 10: "🔴", 20: "⭐️"}
    message = STOCK_STATUS_HEADER
    
    for vol, emoji in volume_emojis.items():
        count = stock.get(vol, 0)
        if count < 5:
            status = "🔴"
        elif count <= 10:
            status = "🟡"
        else:
            status = "🟢"
        message += f"{emoji} {vol}GB: {count} عدد {status}\n"
    
    await query.edit_message_text(message, reply_markup=admin_inventory_keyboard())

# ============== مدیریت قیمت‌ها ==============
@require_auth
async def view_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with async_session() as session:
        prices = await PriceService.get_all_prices(session)
    
    volume_emojis = {1: "🟢", 2: "🔵", 3: "🟣", 5: "🟠", 10: "🔴", 20: "⭐️"}
    message = PRICE_LIST_HEADER.format(datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    for vol, price in prices.items():
        emoji = volume_emojis.get(vol, "⚪️")
        message += f"{emoji} **{vol}GB**: {price:,} تومان\n"
    
    await query.edit_message_text(message, reply_markup=admin_prices_keyboard())

@require_auth
async def edit_price_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ حجم مورد نظر:", reply_markup=volume_selection_keyboard("edit_price"))
    return CHOOSE_VOLUME_PRICE

@require_auth
async def edit_price_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    volume = int(query.data.split("_")[2])
    context.user_data['editing_volume'] = volume
    
    async with async_session() as session:
        current_price = await PriceService.get_price(session, volume)
    
    await query.edit_message_text(EDIT_PRICE_PROMPT.format(volume, f"{current_price:,}"))
    return ENTER_NEW_PRICE

@require_auth
async def save_new_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    volume = context.user_data.get('editing_volume')
    
    try:
        new_price = int(update.message.text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("❌ عدد معتبر وارد کن!")
        return ENTER_NEW_PRICE
    
    async with async_session() as session:
        success = await PriceService.update_price(session, volume, new_price)
    
    if success:
        await update.message.reply_text(
            PRICE_UPDATED.format(volume, f"{new_price:,}", datetime.now().strftime("%H:%M:%S")),
            reply_markup=admin_prices_keyboard()
        )
    else:
        await update.message.reply_text("❌ خطا!", reply_markup=admin_main_keyboard())
    
    return ConversationHandler.END

# ============== مدیریت کاربران ==============
@require_auth
async def search_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(SEARCH_USER_PROMPT)
    return SEARCH_USER

@require_auth
async def search_user_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    
    async with async_session() as session:
        user = await UserService.search_user(session, query_text)
    
    if user:
        status = "🚫 مسدود" if user.is_blocked else "✅ فعال"
        message = (
            f"👤 **اطلاعات کاربر**\n\n"
            f"🆔 آیدی: `{user.telegram_id}`\n"
            f"👤 نام: {user.first_name}\n"
            f"📎 یوزرنیم: @{user.username or 'ندارد'}\n"
            f"💰 موجودی: {user.wallet_balance:,} تومان\n"
            f"📅 عضویت: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"🚦 وضعیت: {status}"
        )
        await update.message.reply_text(message, reply_markup=admin_users_keyboard())
    else:
        await update.message.reply_text("❌ کاربری پیدا نشد!", reply_markup=admin_users_keyboard())
    
    return ConversationHandler.END

@require_auth
async def charge_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(CHARGE_WALLET_PROMPT)
    return CHARGE_USER_ID

@require_auth
async def charge_wallet_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data['charge_user_id'] = user_id
    except ValueError:
        await update.message.reply_text("❌ آیدی عددی معتبر وارد کن!")
        return CHARGE_USER_ID
    
    await update.message.reply_text(CHARGE_AMOUNT_PROMPT)
    return CHARGE_AMOUNT

@require_auth
async def charge_wallet_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('charge_user_id')
    
    try:
        amount = int(update.message.text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("❌ مبلغ معتبر وارد کن!")
        return CHARGE_AMOUNT
    
    async with async_session() as session:
        success = await UserService.charge_wallet(session, user_id, amount, update.effective_user.id)
    
    if success:
        await update.message.reply_text(
            CHARGE_SUCCESS.format(user_id, f"{amount:,}", datetime.now().strftime("%H:%M:%S")),
            reply_markup=admin_users_keyboard()
        )
    else:
        await update.message.reply_text("❌ کاربر پیدا نشد!", reply_markup=admin_users_keyboard())
    
    return ConversationHandler.END

# ============== گزارشات ==============
@require_auth
async def sales_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    days = int(query.data.split("_")[1])
    period_names = {1: "امروز", 7: "این هفته", 30: "این ماه"}
    
    async with async_session() as session:
        sold_configs = await InventoryService.get_sold_configs_by_period(session, days)
        prices = await PriceService.get_all_prices(session)
    
    total_revenue = 0
    volume_stats = {}
    
    for config in sold_configs:
        vol = config.volume_gb
        price = prices.get(vol, 0)
        total_revenue += price
        volume_stats[vol] = volume_stats.get(vol, 0) + 1
    
    volume_emojis = {1: "🟢", 2: "🔵", 3: "🟣", 5: "🟠", 10: "🔴", 20: "⭐️"}
    
    message = f"📊 **گزارش فروش {period_names[days]}**\n\n"
    message += f"🛒 تعداد فروش: {len(sold_configs)}\n"
    message += f"💰 درآمد کل: {total_revenue:,} تومان\n\n"
    
    if volume_stats:
        message += "📦 **تفکیک حجم:**\n"
        for vol, count in sorted(volume_stats.items()):
            emoji = volume_emojis.get(vol, "⚪️")
            message += f"{emoji} {vol}GB: {count} عدد\n"
    
    await query.edit_message_text(message, reply_markup=admin_reports_keyboard())

@require_auth
async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with async_session() as session:
        stats = await UserService.get_user_stats(session)
    
    message = (
        f"📊 **آمار کاربران**\n\n"
        f"👥 کل کاربران: {stats['total_users']}\n"
        f"🆕 کاربران جدید امروز: {stats['new_today']}\n"
        f"💰 مجموع موجودی کیف پول‌ها: {stats['total_balance']:,} تومان\n"
    )
    
    await query.edit_message_text(message, reply_markup=admin_users_keyboard())

# ============== لغو ==============
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=admin_main_keyboard())
    return ConversationHandler.END

# ============== کانورسیشن هندلرها ==============
add_config_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_config_start, pattern="^admin_add_config$")],
    states={
        CHOOSE_VOLUME_ADD: [CallbackQueryHandler(add_config_volume, pattern="^add_vol_")],
        COLLECT_LINKS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, collect_links),
            CommandHandler("done", done_collecting)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

edit_price_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(edit_price_select, pattern="^admin_edit_price_select$")],
    states={
        CHOOSE_VOLUME_PRICE: [CallbackQueryHandler(edit_price_enter, pattern="^edit_price_")],
        ENTER_NEW_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_price)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

search_user_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(search_user_start, pattern="^admin_search_user$")],
    states={
        SEARCH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_user_result)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

charge_wallet_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(charge_wallet_start, pattern="^admin_charge_wallet$")],
    states={
        CHARGE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, charge_wallet_user)],
        CHARGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, charge_wallet_execute)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# ============== لیست هندلرها ==============
admin_handlers = [
    CommandHandler("start", admin_start),
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_admin_password),
    CallbackQueryHandler(admin_logout, pattern="^admin_logout$"),
    CallbackQueryHandler(admin_menu_navigation, pattern="^(admin_main|admin_inventory_menu|admin_prices_menu|admin_users_menu|admin_reports_menu)$"),
    CallbackQueryHandler(stock_status, pattern="^admin_stock_status$"),
    CallbackQueryHandler(view_prices, pattern="^admin_view_prices$"),
    CallbackQueryHandler(sales_report, pattern="^report_"),
    CallbackQueryHandler(user_stats, pattern="^admin_user_stats$"),
    add_config_conv,
    edit_price_conv,
    search_user_conv,
    charge_wallet_conv,
]