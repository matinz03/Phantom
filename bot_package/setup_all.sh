#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r bot_package/requirements.txt

if [ ! -f ".env" ]; then
  cat > .env <<'EOFENV'
MAIN_BOT_TOKEN=
ADMIN_BOT_TOKEN=
ADMIN_USER_ID=
ADMIN_PASSWORD=
DB_URL=sqlite+aiosqlite:///vpn_shop.db
EOFENV
  echo "Created .env. Fill in the Telegram tokens, admin ID, and admin password before running."
fi

echo "Setup complete. Run: source venv/bin/activate && python -m bot_package.run"
