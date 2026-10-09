# 💎 VIP Subscription Bot

> **Production-grade Telegram Bot for automated private channel memberships and payment workflows.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.31-blueviolet.svg)](https://aiogram.dev/)
[![Tests](https://img.shields.io/badge/Tests-13%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-lightgrey.svg)]()

[O'zbekcha Versiya](README.md) | [Русская Версия](README.ru.md)

---

## 📌 Project Overview

**VIP Subscription Bot** is an automated membership management system built with Aiogram 3.x for private Telegram channels, closed trading clubs, and premium content creators.

The bot showcases flexible subscription plans, collects payments (Card, Payme, Click, USDT TRC-20), presents proof of payment to administrators, issues **single-use revocable invite links** (`member_limit=1`), sends renewal reminders 24 hours prior to expiration, and automatically removes expired members from the private channel.

---

## ✨ Key Features

1. **Configurable Subscription Plans:**
   - 30-day, 90-day, 365-day, and custom administrative tiers.
2. **Multi-Payment Invoicing:**
   - Payme, Click, and Crypto (USDT TRC-20) details displayed with dynamic amount formatting.
   - Receipt submission flow where users upload transfer screenshots.
3. **Admin Verification Dashboard:**
   - Realtime payment verification notifications sent to admin chats with photo receipts.
   - One-click inline **Approve** or **Reject** action buttons.
4. **Single-Use Revocable Invite Links:**
   - Generates unique invite links limited to exactly 1 join event (`member_limit=1`), preventing unauthorized sharing.
5. **Automated Expiry Worker:**
   - Autonomous background task continuously checking subscription lifecycle.
   - 24-hour expiration reminder alerts.
   - Immediate automatic channel expulsion (ban + unban) upon plan expiration.
6. **Analytics & Metrics:**
   - `/admin` and `/stats` command reporting total users, active VIPs, pending transactions, and gross revenue.

---

## 🏛 Clean Architecture

```
src/vip_bot/
├── config.py                 # Pydantic V2 environment settings
├── bot.py                    # Bot & Dispatcher DI configuration
├── main.py                   # Async entrypoint & polling orchestrator
├── database/
│   ├── models.py             # User, Plan, Subscription, Payment models
│   └── repository.py         # Async SQLite CRUD & transaction queries
├── services/
│   ├── channel_service.py    # Telegram invite links & member eviction
│   ├── payment_service.py    # Payment requisites & receipt verification
│   └── subscription_service.py # Membership granting & expiry calculations
├── workers/
│   └── expiry_worker.py      # Background task for reminders & kicks
└── handlers/
    ├── user_handlers.py      # /start, /plans, /status, receipt submission
    └── admin_handlers.py     # /admin, /stats, payment approvals
```

---

## 🚀 Installation & Quick Start

### 1. Requirements
- Python 3.10+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- VIP Channel ID (Bot must be an Administrator in the channel with *Invite Users via Link* and *Ban Users* privileges).

### 2. Setup
```bash
git clone https://github.com/afzalbek-dev/vip-subscription-bot.git
cd vip-subscription-bot
pip install -r requirements.txt
pip install -e .
```

### 3. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN, ADMIN_IDS, and VIP_CHANNEL_ID
```

### 4. Run the Bot
```bash
python3 -m vip_bot.main
```

---

## 🧪 Testing Suite (Pytest)

Run all unit and integration tests:
```bash
pytest -v
```

All **13 tests** pass successfully:
- Configuration parsing & admin permissions: **PASSED**
- Plan seeding & SQLite schema initialization: **PASSED**
- User & payment lifecycle CRUD: **PASSED**
- Subscription creation & duration extension: **PASSED**
- Channel invite link generation & member eviction: **PASSED**
- 24h reminder notification & automated eviction worker: **PASSED**

---

## 🐳 Docker Deployment

```bash
docker compose up -d --build
```

---

## 🔒 Security

- Secret credentials and payment cards are loaded exclusively via environment variables (`.env`).
- Single-use invite links prevent unauthorized sharing.
- Admin commands are restricted by strict Telegram User ID checks.

---

## 📄 License

MIT License. Developed by [Afzalbek](https://github.com/afzalbek-dev).
