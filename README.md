# Phantom VPN Bot Suite

Phantom is an asynchronous dual-bot Telegram system for selling VPN subscription links.

- **Main bot:** user-facing shop, wallet balance, purchases, and purchase history.
- **Admin bot:** inventory, prices, wallet charging, user lookup, and sales reports.

The implementation uses Python, `python-telegram-bot`, async SQLAlchemy, and SQLite by default.

## Project Structure

```text
Phantom/
  bot_package/
    main_bot.py
    admin_bot.py
    config_loader.py
    database.py
    models.py
    auth.py
    handlers/
    services/
    utils/
    requirements.txt
    setup_all.sh
    run.py
  README.md
```

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r bot_package/requirements.txt
```

Create a `.env` file in the project root:

```dotenv
MAIN_BOT_TOKEN=123456:ABC-DEF1234
ADMIN_BOT_TOKEN=654321:XYZ-ABC9876
ADMIN_USER_ID=123456789
ADMIN_PASSWORD=replace-with-a-strong-password
DB_URL=sqlite+aiosqlite:///vpn_shop.db
```

Run both bots:

```bash
python -m bot_package.run
```

You can also run the helper script on Linux:

```bash
chmod +x bot_package/setup_all.sh
./bot_package/setup_all.sh
```

## Security Notes

- Do not commit `.env` files or bot tokens.
- Replace the admin password before running the bot.
- SQLite is the default for local and small deployments. Use PostgreSQL before running high-volume paid traffic.

## Current Capabilities

- User registration on `/start`
- Wallet balance display
- Volume-based VPN purchase flow
- Purchase history
- Admin password session
- Admin stock loading from subscription links
- Admin price editing
- Admin wallet charging
- Basic sales and user reports
