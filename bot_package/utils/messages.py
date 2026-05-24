from ..config_loader import BotConfig

SUPPORT_HANDLE = BotConfig.SUPPORT_HANDLE
CHANNEL_HANDLE = BotConfig.CHANNEL_HANDLE

MAIN_MENU_TEXT = """
**Welcome to Phantom VPN**

Secure VPN subscription links with instant delivery after purchase.
Choose an option from the menu below.
"""

WALLET_TEXT = """
**Your wallet**

Current balance: **{} toman**

To top up your wallet, contact support:
{}
"""

BUY_MENU_TEXT = """
**Choose a subscription volume**

All plans are delivered as subscription links immediately after purchase.
"""

PURCHASE_SUCCESS = """
**Purchase complete**

Volume: {} GB
Amount: {} toman

Your subscription link:
`{}`

Save this link and do not share it with others.
"""

HELP_TEXT = f"""
**How to use Phantom**

1. Contact support to charge your wallet.
2. Choose a volume from the buy menu.
3. The bot sends your subscription link after your wallet is charged.
4. Add the link to your VPN client.

Support: {BotConfig.SUPPORT_HANDLE}
Channel: {BotConfig.CHANNEL_HANDLE}
"""

NO_PURCHASE = """
**No purchases yet**

Buy a subscription from the main menu to see it here.
"""

AUTH_ENTER_PASSWORD = """
**Admin login**

Enter your admin password. The password message will be deleted after verification.
"""

AUTH_SUCCESS = """
**Authentication successful**

Welcome to the admin panel.
"""

AUTH_FAILED = """
**Wrong password**

Please try again.
"""

AUTH_EXPIRED = """
**Session expired**

Enter your admin password again.
"""

AUTH_REQUIRED = """
**Authentication required**

Enter your admin password to continue.
"""

ADMIN_MAIN_MENU = """
**Phantom admin panel**

Welcome, {}.
Choose an action:
"""

ADMIN_INVENTORY_MENU = """
**Inventory management**

Add and review VPN subscription stock.
"""

ADMIN_PRICES_MENU = """
**Price management**

View and update plan prices.
"""

ADMIN_USERS_MENU = """
**User management**

Search users, charge wallets, and review user stats.
"""

ADMIN_REPORTS_MENU = """
**Sales reports**

Review sales by period.
"""

ADD_CONFIG_VOLUME = """
**Add VPN configs**

Choose the volume for the links you want to add.
"""

SEND_LINKS_PROMPT = """
**Send subscription links**

Send one or more links. Each line can contain one link.
Supported protocols: http, https, vmess, vless, trojan, ss, ssr, tuic, hysteria, hysteria2.

Send /done when finished or /cancel to stop.
"""

LINKS_DETECTED = """
Added {} new links.
Collected links in this batch: {}

Keep sending links or send /done.
"""

NO_LINKS_FOUND = """
No valid subscription links were found. Try again or send /cancel.
"""

STOCK_STATUS_HEADER = """
**Inventory status**

Critical: fewer than 5
Medium: 5 to 10
Healthy: more than 10

"""

PRICE_LIST_HEADER = """
**Current prices**

Last checked: {}

"""

EDIT_PRICE_PROMPT = """
**Edit price**

Current price for {}GB: {} toman

Enter the new price in toman.
Example: 25000
"""

PRICE_UPDATED = """
**Price updated**

Volume: {}GB
New price: {} toman
Time: {}
"""

SEARCH_USER_PROMPT = """
**Search user**

Enter a numeric Telegram ID or username.
Example: `123456789` or `@username`
"""

CHARGE_WALLET_PROMPT = """
**Charge wallet**

Enter the user's numeric Telegram ID.
"""

CHARGE_AMOUNT_PROMPT = """
**Charge amount**

Enter the amount to add in toman.
Example: 50000
"""

CHARGE_SUCCESS = """
**Wallet charged**

User: `{}`
Amount: {} toman
Time: {}
"""
