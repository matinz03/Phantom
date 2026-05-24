# 🤖 Phantom VPN Bot Suite

**A professional, secure, and fully asynchronous dual-bot system for automated VPN subscription sales on Telegram. Built with modern Python (3.13+), SQLAlchemy, and the latest Telegram Bot API (v21+).**

![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-7.0%2B-0099cc)

---

## 📖 Project Overview

**Phantom** is a complete VPN shop solution operating through two separate Telegram bots:

1.  **Public Sales Bot** (`main_bot`): User-facing bot for purchasing VPN subscriptions via a wallet system.
2.  **Private Admin Bot** (`admin_bot`): Secure management panel for inventory, pricing, user management, and sales reports, protected by password authentication.

The system is designed for **reliability, security, and ease of debugging by AI tools**, with clear separation of concerns, strongly typed async database operations, and comprehensive logging.

---

## 🏗️ Architecture & Project Structure

The project follows a modular, service-oriented architecture optimized for clarity and AI-assisted debugging.

Phantom/
├── bot_package/
│ ├── init.py
│ ├── main_bot.py # Public bot application
│ ├── admin_bot.py # Admin bot application
│ ├── config_loader.py # Environment & configuration management
│ ├── database.py # Async SQLAlchemy engine & session
│ ├── models.py # ORM models (User, Config, Purchase, etc.)
│ ├── auth.py # Admin session & password management
│ ├── handlers/
│ │ ├── init.py
│ │ ├── user_handlers.py # User command & callback handlers
│ │ └── admin_handlers.py # Admin conversation & callback handlers
│ ├── services/
│ │ ├── init.py
│ │ ├── inventory_service.py # Business logic for VPN config stock
│ │ ├── price_service.py # Dynamic price management logic
│ │ └── user_service.py # User search, wallet, and stats logic
│ └── utils/
│ ├── init.py
│ ├── keyboards.py # All inline & reply keyboards (with emojis)
│ ├── messages.py # All user-facing text messages
│ └── validators.py # Input validation (links, etc.)
├── .env # Sensitive configuration (tokens, passwords)
├── .gitignore
├── run.py # Entry point to run both bots concurrently
├── setup_all.sh # One-click project setup script for Linux
└── README.md # This file

### Core Design Principles for AI Debugging

1.  **Explicit Imports:** Every file uses absolute imports relative to the `bot_package` root.
2.  **Type Hinting:** All service and model methods use Python type hints for better static analysis.
3.  **Separation of Concerns:**
    - `handlers/` → Route Telegram updates.
    - `services/` → Contain all business logic and database queries.
    - `utils/` → Provide static data (keyboards, messages) and validation.
4.  **Async by Default:** All database operations are asynchronous using `SQLAlchemy[asyncio]` and `aiosqlite`.

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python** 3.13 or later
- **A Linux VPS** (Ubuntu 24.04 LTS recommended) or local environment
- **Two Telegram Bot Tokens** from [@BotFather](https://t.me/BotFather)
- **Your Telegram Numerical ID** from [@userinfobot](https://t.me/userinfobot)

### Installation (Fresh VPS)

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Ehsoon05/Phantom.git
    cd Phantom
    ```

2.  **Run the setup script:**

    ```bash
    chmod +x setup_all.sh
    sudo bash setup_all.sh
    This script will create the virtual environment, install all dependencies, and prompt you to configure the .env file.
    ```

3.  **Configure .env:**
    Open the .env file and fill in your details:

        ```dotenv
        MAIN_BOT_TOKEN=123456:ABC-DEF1234gh...
        ADMIN_BOT_TOKEN=654321:XYZ-ABC9876ij...
        ADMIN_USER_ID=123456789
        ADMIN_PASSWORD=YourSecurePassword123
        DB_URL=sqlite+aiosqlite:///vpn_shop.db
        ```

4.  **Start the bots:**
    ```bash
    source venv/bin/activate
    python run.py
    ```

## 🛡️ Security

- Admin bot requires password on every sensitive action
- Password messages are auto-deleted
- Sessions expire after 30 minutes

## 🗄️ Database

SQLite via SQLAlchemy async. Models: User, Config, Purchase, Transaction, Price

## 🐞 For AI Debugging

When debugging, always specify:

1. Which file has the error
2. Full error traceback
3. What user action triggered it
4. Relevant service/handler name
