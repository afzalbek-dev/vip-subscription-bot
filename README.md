# 💎 VIP Subscription Bot

> **Telegram VIP kanal va guruh a'zoligini to'liq avtomatlashtirilgan boshqarish boti.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.31-blueviolet.svg)](https://aiogram.dev/)
[![Tests](https://img.shields.io/badge/Tests-13%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-lightgrey.svg)]()

[English Version](README.en.md) | [Русская Версия](README.ru.md)

---

## 📌 Loyiha Haqida

**VIP Subscription Bot** — bu Telegramdagi yopiq (pullik) VIP kanallar va premium hamjamiyatlar uchun to'liq avtomatlashtirilgan obuna boshqaruv tizimi.

Bot obuna tariflarini taqdim etadi, to'lov cheklarini (Payme, Click, USDT TRC-20) qabul qiladi, administrator tasdiqlashi bilan **bir martalik revocable taklif havolasi** (`member_limit=1`) beradi, obuna muddati tugashidan 24 soat oldin ogohlantiradi va muddati tugagach kanaldan avtomatik chiqaradi.

---

## ✨ Asosiy Imkoniyatlar

1. **Moslashuvchan Obuna Tariflari:**
   - 1 oylik (30 kun), 3 oylik (90 kun), 1 yillik (365 kun) va administrator tomonidan maxsus yaratiladigan tariflar.
2. **Ko'p Kanalli To'lov Tizimi:**
   - Payme, Click va USDT (TRC-20) rekvizitlari va avtomatik hisob-faktura.
   - Foydalanuvchi to'lov kvitansiyasini (skrinshot) to'g'ridan-to'g'ri botga yuboradi.
3. **Administrator Tasdiqlash Paneli:**
   - Administratorlar yangi to'lov chekini skrinshoti va foydalanuvchi ma'lumotlari bilan qabul qiladi.
   - Inline tugmalar orqali bir bosishda **Tasdiqlash (Approve)** yoki **Rad etish (Reject)**.
4. **Xavfsiz Bir Martalik Taklif Havolalari:**
   - To'lov tasdiqlangach, Telegram Bot API orqali faqat 1 kishi kirishi mumkin bo'lgan (`member_limit=1`) noyob havola generatsiya qilinadi. Havolani boshqalarga ulashib bo'lmaydi.
5. **Avtomatik Muddati Tugash Nazorati (Expiry Worker):**
   - Orqa fonda mustaqil ishlovchi asinxron monitoring xizmati (`ExpiryWorker`).
   - Obuna tugashiga 24 soat qolganda eslatma xabarnomasi.
   - Obuna muddati tugagan a'zolarni kanaldan avtomatik chiqarish (ban + unban) va ogohlantirish.
6. **Administrator Statistikasi:**
   - Jami foydalanuvchilar, faol a'zolar, kutilayotgan to'lovlar va umumiy tushum hisoboti (`/admin`, `/stats`).

---

## 🏛 Arxitektura

```
src/vip_bot/
├── config.py                 # Pydantic V2 sozlamalari (.env)
├── bot.py                    # Bot va Dispatcher dependency injection
├── main.py                   # Asosiy ishga tushirish va polling
├── database/
│   ├── models.py             # User, Plan, Subscription, Payment modellari
│   └── repository.py         # aiosqlite asinxron CRUD va tranzaksiyalar
├── services/
│   ├── channel_service.py    # Kanalga taklif havolasi va a'zolarni chiqarish
│   ├── payment_service.py    # To'lov tekshiruvi va rekvizitlar
│   └── subscription_service.py # A'zolik muddatini hisoblash va berish
├── workers/
│   └── expiry_worker.py      # Avtomatik 24h eslatma va chiqarish xizmati
└── handlers/
    ├── user_handlers.py      # /start, /plans, /status, kvitansiya qabul qilish
    └── admin_handlers.py     # /admin, /stats, to'lovni tasdiqlash/rad etish
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Talablar
- Python 3.10+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- VIP Kanal ID (Bot kanalda administrator bo'lishi va *Invite Users via Link* hamda *Ban Users* ruxsatlariga ega bo'lishi shart).

### 2. O'rnatish
```bash
git clone https://github.com/afzalbek-dev/vip-subscription-bot.git
cd vip-subscription-bot
pip install -r requirements.txt
pip install -e .
```

### 3. Muhitni Sozlash
```bash
cp .env.example .env
# .env faylini ochib BOT_TOKEN, ADMIN_IDS va VIP_CHANNEL_ID ni kiriting
```

### 4. Ishga Tushirish
```bash
python3 -m vip_bot.main
```

---

## 🧪 Testlash (Pytest)

Barcha unit va integratsion testlar:
```bash
pytest -v
```

Barcha **13 ta test** muvaffaqiyatli bajariladi:
- Konfiguratsiya va admin ruxsatlari: **PASSED**
- SQLite repozitoriy va tariflar avtomatik yaratilishi: **PASSED**
- Foydalanuvchilar va to'lovlar CRUD: **PASSED**
- Obunani yaratish va muddatini uzaytirish: **PASSED**
- Kanal taklif havolalari va a'zolarni chiqarish: **PASSED**
- 24h eslatma va avtomatik chiqarish workeri: **PASSED**

---

## 🐳 Docker Orqali Ishga Tushirish

```bash
docker compose up -d --build
```

---

## 🔒 Xavfsizlik Qoidalari

1. Bot tokeni va admin ID'lari faqat `.env` orqali beriladi va repozitoriyga kiritilmaydi.
2. Taklif havolalari faqat 1 martalik yaratilib, guruh havolasini boshqalarga tarqatishning oldi olinadi.
3. Administrator buyruqlari faqat `ADMIN_IDS` ro'yxatidagi foydalanuvchilar uchun ochiq.

---

## 📄 Litsenziya

MIT License. Muallif: [Afzalbek](https://github.com/afzalbek-dev).
