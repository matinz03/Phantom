
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ============== کیبوردهای کاربر ==============
def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("🛒 خرید اشتراک", callback_data="buy_menu")],
        [
            InlineKeyboardButton("💳 کیف پول", callback_data="wallet_menu"),
            InlineKeyboardButton("📦 اشتراک‌های من", callback_data="history_menu"),
        ],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/YourSupport"),
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help_menu"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)

def buy_volume_keyboard(prices: dict = None):
    if not prices:
        prices = {1: 15000, 2: 28000, 3: 40000, 5: 65000, 10: 120000, 20: 220000}
    
    volume_emojis = {1: "🟢", 2: "🔵", 3: "🟣", 5: "🟠", 10: "🔴", 20: "⭐️"}
    
    buttons = []
    row = []
    for vol, price in prices.items():
        emoji = volume_emojis.get(vol, "⚪️")
        row.append(InlineKeyboardButton(f"{emoji} {vol}GB | {price:,}T", callback_data=f"buy_{vol}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def wallet_keyboard():
    buttons = [
        [InlineKeyboardButton("📞 تماس با پشتیبانی", url="https://t.me/YourSupport")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(buttons)

def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]])

# ============== کیبوردهای ادمین ==============
def admin_main_keyboard():
    buttons = [
        [InlineKeyboardButton("📦 مدیریت انبار", callback_data="admin_inventory_menu")],
        [InlineKeyboardButton("💰 مدیریت قیمت‌ها", callback_data="admin_prices_menu")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users_menu")],
        [InlineKeyboardButton("📊 گزارشات فروش", callback_data="admin_reports_menu")],
        [InlineKeyboardButton("🚪 خروج", callback_data="admin_logout")],
    ]
    return InlineKeyboardMarkup(buttons)

def admin_inventory_keyboard():
    buttons = [
        [InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="admin_add_config")],
        [InlineKeyboardButton("📊 موجودی انبار", callback_data="admin_stock_status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def volume_selection_keyboard(prefix="add_vol"):
    volume_emojis = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 5: "5️⃣", 10: "🔟", 20: "2️⃣0️⃣"}
    buttons = []
    row = []
    for vol, emoji in volume_emojis.items():
        row.append(InlineKeyboardButton(f"{emoji} {vol}GB", callback_data=f"{prefix}_{vol}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 انصراف", callback_data="admin_main")])
    return InlineKeyboardMarkup(buttons)

def admin_prices_keyboard():
    buttons = [
        [InlineKeyboardButton("📋 مشاهده قیمت‌ها", callback_data="admin_view_prices")],
        [InlineKeyboardButton("✏️ ویرایش قیمت", callback_data="admin_edit_price_select")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def admin_users_keyboard():
    buttons = [
        [InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user")],
        [InlineKeyboardButton("💳 شارژ کیف پول", callback_data="admin_charge_wallet")],
        [InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_user_stats")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)

def admin_reports_keyboard():
    buttons = [
        [InlineKeyboardButton("📈 امروز", callback_data="report_1")],
        [InlineKeyboardButton("📈 این هفته", callback_data="report_7")],
        [InlineKeyboardButton("📈 این ماه", callback_data="report_30")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)