"""Async SQLite Database Repository for VIP Subscription Bot."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
import aiosqlite

from vip_bot.database.models import User, Plan, Subscription, Payment

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DatabaseRepository:
    """Manages all persistent database operations using aiosqlite."""

    def __init__(self, db_path: Path):
        self.db_path = str(db_path)

    async def init_db(self) -> None:
        """Create database tables and indexes if they do not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    duration_days INTEGER NOT NULL,
                    price_uzs INTEGER NOT NULL,
                    price_usd REAL NOT NULL,
                    description TEXT,
                    is_active INTEGER DEFAULT 1
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_id TEXT NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    status TEXT DEFAULT 'active',
                    reminder_sent INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (plan_id) REFERENCES plans(id)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    receipt_file_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (plan_id) REFERENCES plans(id)
                );
            """)

            await db.commit()
            logger.info("Database schema initialized successfully.")

        await self._seed_default_plans()

    async def _seed_default_plans(self) -> None:
        """Populate initial subscription tiers if table is empty."""
        default_plans = [
            Plan("vip_30", "VIP 1 Oy (30 kun)", 30, 100000, 8.0, "1 oylik to'liq VIP kanal obunasi"),
            Plan("vip_90", "VIP 3 Oy (90 kun)", 90, 250000, 20.0, "3 oylik VIP kanal obunasi (15% chegirma)"),
            Plan("vip_365", "VIP 1 Yil (365 kun)", 365, 800000, 65.0, "Yillik VIP obuna (Eng tejamkor)"),
        ]

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM plans")
            count = (await cursor.fetchone())[0]
            if count == 0:
                for p in default_plans:
                    await db.execute(
                        "INSERT INTO plans (id, name, duration_days, price_uzs, price_usd, description, is_active) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (p.id, p.name, p.duration_days, p.price_uzs, p.price_usd, p.description, 1),
                    )
                await db.commit()
                logger.info("Seeded default VIP plans.")

    # User operations
    async def upsert_user(self, user: User) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
                """,
                (user.user_id, user.username, user.full_name),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, username, full_name, created_at FROM users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        user_id=row[0],
                        username=row[1],
                        full_name=row[2],
                        created_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3],
                    )
                return None

    # Plan operations
    async def get_plans(self, only_active: bool = True) -> List[Plan]:
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT id, name, duration_days, price_uzs, price_usd, description, is_active FROM plans"
            if only_active:
                query += " WHERE is_active = 1"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [
                    Plan(
                        id=r[0],
                        name=r[1],
                        duration_days=r[2],
                        price_uzs=r[3],
                        price_usd=r[4],
                        description=r[5] or "",
                        is_active=bool(r[6]),
                    )
                    for r in rows
                ]

    async def get_plan(self, plan_id: str) -> Optional[Plan]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, name, duration_days, price_uzs, price_usd, description, is_active FROM plans WHERE id = ?",
                (plan_id,),
            ) as cursor:
                r = await cursor.fetchone()
                if r:
                    return Plan(
                        id=r[0],
                        name=r[1],
                        duration_days=r[2],
                        price_uzs=r[3],
                        price_usd=r[4],
                        description=r[5] or "",
                        is_active=bool(r[6]),
                    )
                return None

    # Payment operations
    async def create_payment(self, payment: Payment) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO payments (user_id, plan_id, amount, currency, payment_method, status, receipt_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment.user_id,
                    payment.plan_id,
                    payment.amount,
                    payment.currency,
                    payment.payment_method,
                    payment.status,
                    payment.receipt_file_id,
                    payment.created_at.isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id, user_id, plan_id, amount, currency, payment_method, status, receipt_file_id, created_at, reviewed_by
                FROM payments WHERE id = ?
                """,
                (payment_id,),
            ) as cursor:
                r = await cursor.fetchone()
                if r:
                    return Payment(
                        id=r[0],
                        user_id=r[1],
                        plan_id=r[2],
                        amount=r[3],
                        currency=r[4],
                        payment_method=r[5],
                        status=r[6],
                        receipt_file_id=r[7],
                        created_at=datetime.fromisoformat(r[8]) if isinstance(r[8], str) else r[8],
                        reviewed_by=r[9],
                    )
                return None

    async def update_payment_status(self, payment_id: int, status: str, reviewed_by: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE payments SET status = ?, reviewed_by = ? WHERE id = ?",
                (status, reviewed_by, payment_id),
            )
            await db.commit()

    # Subscription operations
    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        async with aiosqlite.connect(self.db_path) as db:
            now_iso = utc_now().isoformat()
            async with db.execute(
                """
                SELECT id, user_id, plan_id, start_date, end_date, status, reminder_sent
                FROM subscriptions
                WHERE user_id = ? AND status = 'active' AND end_date > ?
                ORDER BY end_date DESC LIMIT 1
                """,
                (user_id, now_iso),
            ) as cursor:
                r = await cursor.fetchone()
                if r:
                    return Subscription(
                        id=r[0],
                        user_id=r[1],
                        plan_id=r[2],
                        start_date=datetime.fromisoformat(r[3]) if isinstance(r[3], str) else r[3],
                        end_date=datetime.fromisoformat(r[4]) if isinstance(r[4], str) else r[4],
                        status=r[5],
                        reminder_sent=bool(r[6]),
                    )
                return None

    async def create_or_extend_subscription(self, user_id: int, plan_id: str, duration_days: int) -> Subscription:
        """Create a new subscription or extend existing active subscription."""
        async with aiosqlite.connect(self.db_path) as db:
            existing = await self.get_active_subscription(user_id)
            now = utc_now()

            if existing and existing.end_date > now:
                # Extend from existing end date
                new_start = existing.start_date
                new_end = existing.end_date + timedelta(days=duration_days)
                await db.execute(
                    "UPDATE subscriptions SET end_date = ?, reminder_sent = 0 WHERE id = ?",
                    (new_end.isoformat(), existing.id),
                )
                await db.commit()
                existing.end_date = new_end
                existing.reminder_sent = False
                return existing
            else:
                # Brand new subscription
                new_start = now
                new_end = now + timedelta(days=duration_days)
                cursor = await db.execute(
                    """
                    INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status, reminder_sent)
                    VALUES (?, ?, ?, ?, 'active', 0)
                    """,
                    (user_id, plan_id, new_start.isoformat(), new_end.isoformat()),
                )
                await db.commit()
                return Subscription(
                    id=cursor.lastrowid,
                    user_id=user_id,
                    plan_id=plan_id,
                    start_date=new_start,
                    end_date=new_end,
                    status="active",
                    reminder_sent=False,
                )

    async def get_expiring_subscriptions(self, hours: int = 24) -> List[Subscription]:
        """Find active subscriptions expiring within the given hours window where reminder hasn't been sent."""
        async with aiosqlite.connect(self.db_path) as db:
            now = utc_now()
            target_time = now + timedelta(hours=hours)
            async with db.execute(
                """
                SELECT id, user_id, plan_id, start_date, end_date, status, reminder_sent
                FROM subscriptions
                WHERE status = 'active' AND reminder_sent = 0
                  AND end_date > ? AND end_date <= ?
                """,
                (now.isoformat(), target_time.isoformat()),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Subscription(
                        id=r[0],
                        user_id=r[1],
                        plan_id=r[2],
                        start_date=datetime.fromisoformat(r[3]) if isinstance(r[3], str) else r[3],
                        end_date=datetime.fromisoformat(r[4]) if isinstance(r[4], str) else r[4],
                        status=r[5],
                        reminder_sent=bool(r[6]),
                    )
                    for r in rows
                ]

    async def mark_reminder_sent(self, sub_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE subscriptions SET reminder_sent = 1 WHERE id = ?", (sub_id,))
            await db.commit()

    async def get_expired_subscriptions(self) -> List[Subscription]:
        """Find subscriptions that have passed end_date but are still marked active."""
        async with aiosqlite.connect(self.db_path) as db:
            now_iso = utc_now().isoformat()
            async with db.execute(
                """
                SELECT id, user_id, plan_id, start_date, end_date, status, reminder_sent
                FROM subscriptions
                WHERE status = 'active' AND end_date <= ?
                """,
                (now_iso,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Subscription(
                        id=r[0],
                        user_id=r[1],
                        plan_id=r[2],
                        start_date=datetime.fromisoformat(r[3]) if isinstance(r[3], str) else r[3],
                        end_date=datetime.fromisoformat(r[4]) if isinstance(r[4], str) else r[4],
                        status=r[5],
                        reminder_sent=bool(r[6]),
                    )
                    for r in rows
                ]

    async def mark_subscription_expired(self, sub_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE subscriptions SET status = 'expired' WHERE id = ?", (sub_id,))
            await db.commit()

    async def get_stats(self) -> dict:
        """Calculate system metrics for admin dashboard."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            total_users = (await cursor.fetchone())[0]

            now_iso = utc_now().isoformat()
            cursor = await db.execute(
                "SELECT COUNT(*) FROM subscriptions WHERE status = 'active' AND end_date > ?",
                (now_iso,),
            )
            active_subs = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
            pending_payments = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved' AND currency = 'UZS'"
            )
            total_revenue_uzs = (await cursor.fetchone())[0]

            return {
                "total_users": total_users,
                "active_subs": active_subs,
                "pending_payments": pending_payments,
                "total_revenue_uzs": total_revenue_uzs,
            }
