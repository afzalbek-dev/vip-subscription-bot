"""Tests for configuration settings."""

from vip_bot.config import Settings


def test_settings_admin_check():
    settings = Settings(admin_ids=[100, 200, 300])
    assert settings.is_admin(100) is True
    assert settings.is_admin(200) is True
    assert settings.is_admin(999) is False


def test_settings_sqlite_path(temp_db_path):
    settings = Settings(database_url=f"sqlite:///{temp_db_path}")
    assert settings.sqlite_path == temp_db_path
