import pytest
import os
import sqlite3
from unittest.mock import patch
from src import database

@pytest.fixture
def setup_test_db(monkeypatch):
    db_file = os.path.join(os.path.dirname(__file__), "test_database.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass
            
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.setup_db()
    
    yield
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass

class TestDatabaseAdmins:
    def test_add_admin(self, setup_test_db):
        database.add_admin(12345)
        admins = database.get_all_admins()
        assert 12345 in admins
        assert len(admins) == 1

    def test_add_admin_duplicate_ignored(self, setup_test_db):
        database.add_admin(12345)
        database.add_admin(12345)
        admins = database.get_all_admins()
        assert len(admins) == 1
        assert admins[0] == 12345

    def test_remove_admin(self, setup_test_db):
        database.add_admin(12345)
        database.remove_admin(12345)
        admins = database.get_all_admins()
        assert 12345 not in admins
        assert len(admins) == 0

    def test_remove_admin_nonexistent(self, setup_test_db):
        database.remove_admin(99999)
        admins = database.get_all_admins()
        assert len(admins) == 0

    def test_get_all_admins_empty(self, setup_test_db):
        admins = database.get_all_admins()
        assert admins == []

class TestDatabaseTrackedUsers:
    def test_add_tracked_user(self, setup_test_db):
        database.add_tracked_user(54321)
        users = database.get_all_tracked_users()
        assert 54321 in users
        assert len(users) == 1

    def test_add_tracked_user_duplicate_ignored(self, setup_test_db):
        database.add_tracked_user(54321)
        database.add_tracked_user(54321)
        users = database.get_all_tracked_users()
        assert len(users) == 1
        assert users[0] == 54321

    def test_remove_tracked_user(self, setup_test_db):
        database.add_tracked_user(54321)
        database.remove_tracked_user(54321)
        users = database.get_all_tracked_users()
        assert 54321 not in users
        assert len(users) == 0

    def test_remove_tracked_user_nonexistent(self, setup_test_db):
        database.remove_tracked_user(88888)
        users = database.get_all_tracked_users()
        assert len(users) == 0

    def test_get_all_tracked_users_empty(self, setup_test_db):
        users = database.get_all_tracked_users()
        assert users == []

class TestDatabaseGuildConfigs:
    def test_save_and_get_guild_config(self, setup_test_db):
        database.save_guild_config(111, 222, 333)
        config = database.get_guild_config(111)
        assert config is not None
        assert config[0] == 222
        assert config[1] == 333

    def test_update_guild_config(self, setup_test_db):
        database.save_guild_config(111, 222, 333)
        database.save_guild_config(111, 444, 555)
        config = database.get_guild_config(111)
        assert config is not None
        assert config[0] == 444
        assert config[1] == 555

    def test_get_guild_config_nonexistent(self, setup_test_db):
        config = database.get_guild_config(999)
        assert config is None

    def test_delete_guild_config(self, setup_test_db):
        database.save_guild_config(111, 222, 333)
        database.delete_guild_config(111)
        config = database.get_guild_config(111)
        assert config is None

    def test_delete_guild_config_nonexistent(self, setup_test_db):
        database.delete_guild_config(888)
        config = database.get_guild_config(888)
        assert config is None
