# 💎 VIP Subscription Bot

> **Автоматизированный Telegram бот для управления платными VIP каналами и подписками.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.31-blueviolet.svg)](https://aiogram.dev/)
[![Tests](https://img.shields.io/badge/Tests-13%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-lightgrey.svg)]()

[Узбекская Версия](README.md) | [English Version](README.en.md)

---

## 📌 Описание проекта

**VIP Subscription Bot** — это производственная система управления платным доступом в приватные Telegram каналы и закрытые сообщества на базе Aiogram 3.x.

Бот автоматизирует выбор тарифного плана, выставление счетов (Payme, Click, USDT TRC-20), проверку чеков администратором, генерацию **одноразовых отзывных ссылок** (`member_limit=1`), напоминания за 24 часа до окончания срока и автоматическое удаление пользователей по истечении подписки.

---

## ✨ Основные возможности

1. **Гибкие тарифные планы:**
   - 30 дней, 90 дней, 365 дней и настраиваемые административные тарифы.
2. **Мультиканальная оплата:**
   - Поддержка карт (Payme, Click) и криптовалюты (USDT TRC-20).
   - Загрузка скриншотов чеков пользователем прямо в диалог с ботом.
3. **Панель подтверждения для администраторов:**
   - Уведомления администраторам с фото квитанции и данными плательщика.
   - Быстрое подтверждение (**Approve**) или отклонение (**Reject**) через inline-кнопки.
4. **Безопасные одноразовые ссылки-приглашения:**
   - Создание индивидуальной ссылки с лимитом ровно на 1 переход (`member_limit=1`), исключающей передачу доступа третьим лицам.
5. **Фоновый воркер контроля срока (Expiry Worker):**
   - Автоматическая отправка уведомления за 24 часа до истечения тарифа.
   - Автоматическое исключение из канала (ban + unban) и оповещение пользователя по окончании подписки.
6. **Статистика и отчеты:**
   - Команды `/admin` и `/stats` с данными о количестве пользователей, активных VIP, ожидающих заявках и выручке.

---

## 🏛 Архитектура проекта

```
src/vip_bot/
├── config.py                 # Настройки Pydantic V2 и .env
├── bot.py                    # Инициализация Bot и Dispatcher (DI)
├── main.py                   # Точка входа и запуск polling
├── database/
│   ├── models.py             # Модели User, Plan, Subscription, Payment
│   └── repository.py         # Асинхронные операции SQLite через aiosqlite
├── services/
│   ├── channel_service.py    # Управление доступом в канал и ссылки
│   ├── payment_service.py    # Обработка реквизитов и статусов оплаты
│   └── subscription_service.py # Выдача и продление подписок
├── workers/
│   └── expiry_worker.py      # Фоновая служба проверки сроков
└── handlers/
    ├── user_handlers.py      # /start, /plans, /status, отправка чеков
    └── admin_handlers.py     # /admin, /stats, одобрение/отклонение оплаты
```

---

## 🚀 Установка и быстрый запуск

### 1. Требования
- Python 3.10+
- Токен Telegram бота ([@BotFather](https://t.me/BotFather))
- ID VIP канала (бот должен быть администратором канала с правами на приглашение и блокировку участников).

### 2. Установка
```bash
git clone https://github.com/afzalbek-dev/vip-subscription-bot.git
cd vip-subscription-bot
pip install -r requirements.txt
pip install -e .
```

### 3. Настройка окружения
```bash
cp .env.example .env
# Заполните BOT_TOKEN, ADMIN_IDS и VIP_CHANNEL_ID
```

### 4. Запуск
```bash
python3 -m vip_bot.main
```

---

## 🧪 Тестирование (Pytest)

```bash
pytest -v
```

Все **13 тестов** успешно пройдены:
- Проверка прав администратора и конфигов: **PASSED**
- Автоматическая инициализация БД и тарифных планов: **PASSED**
- CRUD операции пользователей и платежей: **PASSED**
- Продление действующих подписок: **PASSED**
- Генерация ссылок и процедура исключения: **PASSED**
- Воркер 24-часовых уведомлений и аннулирования доступа: **PASSED**

---

## 🐳 Развертывание в Docker

```bash
docker compose up -d --build
```

---

## 🔒 Безопасность

- Ключи доступа и токены хранятся строго в `.env` и не попадают в репозиторий.
- Доступ к административным командам ограничен списком `ADMIN_IDS`.

---

## 📄 Лицензия

MIT License. Автор: [Afzalbek](https://github.com/afzalbek-dev).
