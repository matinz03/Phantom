from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..config_loader import BotConfig


def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("Buy subscription", callback_data="buy_menu")],
        [
            InlineKeyboardButton("Wallet", callback_data="wallet_menu"),
            InlineKeyboardButton("My purchases", callback_data="history_menu"),
        ],
        [
            InlineKeyboardButton("Support", url=BotConfig.SUPPORT_URL),
            InlineKeyboardButton("Help", callback_data="help_menu"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def buy_volume_keyboard(prices: dict | None = None):
    if not prices:
        prices = {1: 15000, 2: 28000, 3: 40000, 5: 65000, 10: 120000, 20: 220000}

    buttons = []
    row = []
    for volume, price in prices.items():
        row.append(InlineKeyboardButton(f"{volume}GB | {price:,}T", callback_data=f"buy_{volume}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def wallet_keyboard():
    buttons = [
        [InlineKeyboardButton("Contact support", url=BotConfig.SUPPORT_URL)],
        [InlineKeyboardButton("Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(buttons)


def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Main menu", callback_data="main_menu")]])


def admin_main_keyboard():
    buttons = [
        [InlineKeyboardButton("Inventory", callback_data="admin_inventory_menu")],
        [InlineKeyboardButton("Prices", callback_data="admin_prices_menu")],
        [InlineKeyboardButton("Users", callback_data="admin_users_menu")],
        [InlineKeyboardButton("Reports", callback_data="admin_reports_menu")],
        [InlineKeyboardButton("Log out", callback_data="admin_logout")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_inventory_keyboard():
    buttons = [
        [InlineKeyboardButton("Add config", callback_data="admin_add_config")],
        [InlineKeyboardButton("Stock status", callback_data="admin_stock_status")],
        [InlineKeyboardButton("Back", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def volume_selection_keyboard(prefix="add_vol"):
    volumes = [1, 2, 3, 5, 10, 20]
    buttons = []
    row = []
    for volume in volumes:
        row.append(InlineKeyboardButton(f"{volume}GB", callback_data=f"{prefix}_{volume}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Cancel", callback_data="admin_main")])
    return InlineKeyboardMarkup(buttons)


def admin_prices_keyboard():
    buttons = [
        [InlineKeyboardButton("View prices", callback_data="admin_view_prices")],
        [InlineKeyboardButton("Edit price", callback_data="admin_edit_price_select")],
        [InlineKeyboardButton("Back", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_users_keyboard():
    buttons = [
        [InlineKeyboardButton("Search user", callback_data="admin_search_user")],
        [InlineKeyboardButton("Charge wallet", callback_data="admin_charge_wallet")],
        [InlineKeyboardButton("User stats", callback_data="admin_user_stats")],
        [InlineKeyboardButton("Back", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_reports_keyboard():
    buttons = [
        [InlineKeyboardButton("Today", callback_data="report_1")],
        [InlineKeyboardButton("This week", callback_data="report_7")],
        [InlineKeyboardButton("This month", callback_data="report_30")],
        [InlineKeyboardButton("Back", callback_data="admin_main")],
    ]
    return InlineKeyboardMarkup(buttons)
