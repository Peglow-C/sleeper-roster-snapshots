"""
Tests for sleeper_roster_snapshot.py at one seam: a whole run through main(),
with Sleeper's API (requests.get) and Discord's webhook (requests.post) faked.

Run with: .venv/bin/python -m unittest
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests

import sleeper_roster_snapshot as snap

WEBHOOK = "https://discord.test/api/webhooks/1/abc"
ME = "u1"
LEAGUES = [
    {"league_id": "L1", "name": "Hard Knocks", "season": "2026", "settings": {}},
    {"league_id": "L2", "name": "Twelve Bolievers", "season": "2026", "settings": {}},
]
PLAYERS = {"p1": {"full_name": "Player One", "position": "QB", "team": "KC"}}


def fake_sleeper(missing_roster_in=(), fail_with=None):
    """Return a requests.get replacement that serves canned Sleeper responses."""
    def get(url, timeout=None):
        if fail_with:
            raise fail_with
        path = url.removeprefix(snap.API_BASE)
        if path == "/user/me":
            body = {"user_id": ME}
        elif path.startswith(f"/user/{ME}/leagues/"):
            body = LEAGUES
        elif path == "/players/nfl":
            body = PLAYERS
        elif path.endswith("/rosters"):
            league_id = path.split("/")[2]
            owner = "someone-else" if league_id in missing_roster_in else ME
            body = [{"owner_id": owner, "players": ["p1"], "starters": ["p1"], "settings": {}}]
        elif path.endswith("/users"):
            body = [{"user_id": ME, "display_name": "me"}]
        else:
            raise AssertionError(f"unexpected Sleeper call: {url}")
        resp = mock.Mock()
        resp.json.return_value = body
        return resp
    return get


class SnapshotRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.post = mock.Mock()
        for patcher in (
            # Never read the real .env, so tests can't post to a real webhook.
            mock.patch.object(snap, "ENV_PATH", self.tmp / "no.env"),
            mock.patch.object(snap, "PLAYERS_CACHE_PATH", self.tmp / "players.json"),
            mock.patch.object(snap.requests, "post", self.post),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, env=None, **sleeper):
        argv = ["sleeper_roster_snapshot.py", "--username", "me", "--outdir", str(self.tmp / "rosters")]
        with mock.patch.dict(os.environ, env or {}, clear=True), \
                mock.patch.object(sys, "argv", argv), \
                mock.patch.object(snap.requests, "get", fake_sleeper(**sleeper)), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                snap.main()
            except SystemExit as e:
                return e.code
            return 0

    def posted(self):
        """The JSON payloads sent to Discord."""
        return [c.kwargs["json"] for c in self.post.call_args_list]

    def test_clean_run_posts_one_ok_message_without_mention(self):
        code = self.run_main(env={"DISCORD_WEBHOOK_URL": WEBHOOK})

        self.assertEqual(code, 0)
        [payload] = self.posted()
        self.assertEqual(self.post.call_args.args[0], WEBHOOK)
        self.assertIn("OK", payload["content"])
        self.assertIn("hard-knocks", payload["content"])
        self.assertIn("twelve-bolievers", payload["content"])
        self.assertNotIn("<@", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})

    def test_ok_message_mentions_success_user_only(self):
        self.run_main(env={"DISCORD_WEBHOOK_URL": WEBHOOK,
                           "DISCORD_SUCCESS_USER_ID": "111",
                           "DISCORD_FAIL_USER_ID": "222"})

        [payload] = self.posted()
        self.assertTrue(payload["content"].startswith("<@111> "))
        self.assertNotIn("222", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"users": ["111"]})

    def test_no_webhook_posts_nothing(self):
        code = self.run_main(env={"DISCORD_SUCCESS_USER_ID": "111"})

        self.assertEqual(code, 0)
        self.post.assert_not_called()

    def test_skipped_league_posts_failure_and_exits_non_zero(self):
        code = self.run_main(env={"DISCORD_WEBHOOK_URL": WEBHOOK,
                                  "DISCORD_SUCCESS_USER_ID": "111",
                                  "DISCORD_FAIL_USER_ID": "222"},
                             missing_roster_in=("L2",))

        self.assertNotEqual(code, 0)
        self.assertEqual(len(list((self.tmp / "rosters").glob("hard-knocks_*.json"))), 1)
        [payload] = self.posted()
        self.assertTrue(payload["content"].startswith("<@222> "))
        self.assertIn("failed", payload["content"])
        self.assertIn("Twelve Bolievers", payload["content"])
        self.assertIn("hard-knocks", payload["content"])
        self.assertEqual(payload["allowed_mentions"], {"users": ["222"]})

    def test_sleeper_api_error_posts_failure_and_keeps_the_error(self):
        boom = requests.ConnectionError("Sleeper unreachable")
        with self.assertRaises(requests.ConnectionError):
            self.run_main(env={"DISCORD_WEBHOOK_URL": WEBHOOK}, fail_with=boom)

        [payload] = self.posted()
        self.assertIn("failed", payload["content"])
        self.assertIn("ConnectionError: Sleeper unreachable", payload["content"])
        self.assertNotIn("<@", payload["content"])

    def test_unknown_username_posts_failure_with_exit_message(self):
        def get(url, timeout=None):
            resp = mock.Mock()
            resp.json.return_value = None  # Sleeper answers null for unknown users
            return resp

        with mock.patch.object(snap.requests, "get", get):
            argv = ["x", "--username", "nobody"]
            with mock.patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": WEBHOOK}, clear=True), \
                    mock.patch.object(sys, "argv", argv), \
                    contextlib.redirect_stdout(io.StringIO()), \
                    self.assertRaises(SystemExit) as cm:
                snap.main()

        self.assertIn("nobody", str(cm.exception.code))
        [payload] = self.posted()
        self.assertIn("Could not find a Sleeper user for username 'nobody'", payload["content"])

    def test_broken_webhook_does_not_hide_the_result(self):
        self.post.side_effect = requests.ConnectionError("Discord down")

        code = self.run_main(env={"DISCORD_WEBHOOK_URL": WEBHOOK}, missing_roster_in=("L2",))

        self.assertNotEqual(code, 0)
        self.assertEqual(self.post.call_count, 1)

    def test_env_file_configures_webhook(self):
        (self.tmp / ".env").write_text(f'# comment\nDISCORD_WEBHOOK_URL="{WEBHOOK}"\nDISCORD_SUCCESS_USER_ID=\n')
        with mock.patch.object(snap, "ENV_PATH", self.tmp / ".env"):
            self.run_main()

        [payload] = self.posted()
        self.assertEqual(self.post.call_args.args[0], WEBHOOK)
        self.assertNotIn("<@", payload["content"])


if __name__ == "__main__":
    unittest.main()
