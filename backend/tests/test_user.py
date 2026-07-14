import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import user


class FakeCursor:
    def __init__(self):
        self.rows = []

    def execute(self, query, params=None):
        if "RETURNING id, email, username, name, role, default_ticker" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA")]
        elif "SELECT id, email, username, name, role, default_ticker, password" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA", "hashed-password")]
        elif "SELECT" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA")]
        else:
            self.rows = []

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def close(self):
        return None


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        return None

    def close(self):
        return None


class UserCrudTests(unittest.TestCase):
    def setUp(self):
        # Set database path to a test database file
        self.test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_watchlist.db"))
        user.SQLITE_DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def tearDown(self):
        # Clean up the test database file
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    @patch("user.get_connection")
    def test_create_user(self, mock_get_connection):
        mock_get_connection.return_value = FakeConnection()

        result = user.create_user({
            "email": "demo@example.com",
            "username": "demo",
            "password": "secret",
            "name": "Demo",
            "role": "Trader",
            "default_ticker": "BBCA",
        })

        self.assertEqual(result["email"], "demo@example.com")
        self.assertEqual(result["username"], "demo")

    @patch("user.get_connection")
    def test_get_user(self, mock_get_connection):
        mock_get_connection.return_value = FakeConnection()

        result = user.get_user(1)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["email"], "demo@example.com")

    def test_watchlist_crud(self):
        # 1. Create a watchlist
        wl = user.create_watchlist(1, {"name": "Tech", "symbols": ["GOTO", "TLKM"]})
        self.assertEqual(wl["user_id"], 1)
        self.assertEqual(wl["name"], "Tech")
        self.assertEqual(wl["symbols"], ["GOTO", "TLKM"])

        # 2. Get watchlists (which returns list of watchlists)
        wls = user.get_watchlists(1)
        self.assertEqual(len(wls), 1)
        self.assertEqual(wls[0]["name"], "Tech")

        # 3. Get specific watchlist
        wl_fetched = user.get_watchlist(1, wl["id"])
        self.assertIsNotNone(wl_fetched)
        self.assertEqual(wl_fetched["name"], "Tech")

        # 4. Update watchlist
        wl_updated = user.update_watchlist(1, wl["id"], {"name": "Tech Updated", "symbols": ["GOTO", "TLKM", "ASII"]})
        self.assertEqual(wl_updated["name"], "Tech Updated")
        self.assertEqual(wl_updated["symbols"], ["GOTO", "TLKM", "ASII"])

        # 5. Delete watchlist
        del_res = user.delete_watchlist(1, wl["id"])
        self.assertTrue(del_res["deleted"])

        # 6. Fetching empty watchlists auto-seeds a default watchlist
        wls_after_delete = user.get_watchlists(1)
        self.assertEqual(len(wls_after_delete), 1)
        self.assertEqual(wls_after_delete[0]["name"], "Daftar Pantau Utama")


if __name__ == "__main__":
    unittest.main()
