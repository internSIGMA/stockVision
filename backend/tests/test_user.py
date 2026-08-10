import os
import sys
import json
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import user

class FakeWatchlistStore:
    def __init__(self):
        self.watchlists = {}
        self.counter = 0

store = FakeWatchlistStore()

class FakeCursor:
    def __init__(self):
        self.rows = []

    def execute(self, query, params=None):
        params = params or ()
        if "RETURNING id, email, username, name, role, default_ticker" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA", "08123456789")]
        elif "SELECT id, email, username, name, role, default_ticker, password" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA", "hashed-password")]
        elif "INSERT INTO idxsaham.watchlists" in query:
            store.counter += 1
            wid = store.counter
            uid = params[0]
            wname = params[1]
            wsyms = params[2]
            store.watchlists[wid] = (wid, uid, wname, wsyms, "2026-08-10 00:00:00")
            if "RETURNING id," in query or "RETURNING id, user_id" in query:
                self.rows = [(wid, uid, wname, wsyms, "2026-08-10 00:00:00")]
            else:
                self.rows = [(wid,)]
        elif "SELECT id FROM idxsaham.watchlists" in query:
            wid = params[1]
            if wid in store.watchlists:
                self.rows = [(wid,)]
            else:
                self.rows = []
        elif "SELECT id, user_id, name, symbols, created_at FROM idxsaham.watchlists WHERE user_id = %s AND id = %s" in query:

            wid = params[1]
            if wid in store.watchlists:
                self.rows = [store.watchlists[wid]]
            else:
                self.rows = []
        elif "SELECT id, user_id, name, symbols, created_at FROM idxsaham.watchlists WHERE user_id = %s" in query:
            uid = params[0]
            matching = [v for k, v in store.watchlists.items() if v[1] == uid]
            self.rows = matching
        elif "UPDATE idxsaham.watchlists" in query:
            wname = params[0]
            wsyms = params[1]
            uid = params[2]
            wid = params[3]
            if wid in store.watchlists:
                store.watchlists[wid] = (wid, uid, wname, wsyms, "2026-08-10 00:00:00")
                self.rows = [store.watchlists[wid]]
            else:
                self.rows = []
        elif "DELETE FROM idxsaham.watchlists" in query:
            wid = params[1]
            store.watchlists.pop(wid, None)
            self.rows = []
        elif "SELECT" in query and "users" in query:
            self.rows = [(1, "demo@example.com", "demo", "Demo", "Trader", "BBCA", "08123456789")]
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
        store.watchlists = {}
        store.counter = 0

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

    @patch("user.get_connection")
    def test_watchlist_crud(self, mock_get_connection):
        mock_get_connection.return_value = FakeConnection()

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
        self.assertEqual(wls_after_delete[0]["name"], "Daftar Utama")

if __name__ == "__main__":
    unittest.main()
