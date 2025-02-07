import unittest
from unittest.mock import patch
from sessions import Sessions, SessionEntry  # Assuming the module name is `sessions`
from account_logon_type import AccountLogonType


class TestSessions(unittest.TestCase):
    def setUp(self):
        self.sessions = Sessions()
        self.email = "test@example.com"
        self.token = "test_token"
        self.auth_type = AccountLogonType.BASIC

    def test_add_session(self):
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertIn(self.email, self.sessions._sessions)
        self.assertEqual(self.sessions._sessions[self.email].token, self.token)
        self.assertEqual(self.sessions._sessions[self.email].authentication_type, self.auth_type)

    def test_add_session_overwrites_existing(self):
        self.sessions.add_session(self.email, "old_token", self.auth_type)
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertEqual(self.sessions._sessions[self.email].token, self.token)  # New token should replace old one

    def test_delete_session(self):
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.sessions.delete_session(self.email)
        self.assertNotIn(self.email, self.sessions._sessions)

    def test_delete_session_nonexistent(self):
        self.sessions.delete_session(self.email)  # Should not raise an error
        self.assertNotIn(self.email, self.sessions._sessions)

    def test_is_valid_session_true(self):
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(self.sessions.is_valid_session(self.email, self.token))

    def test_is_valid_session_false_wrong_token(self):
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertFalse(self.sessions.is_valid_session(self.email, "wrong_token"))

    def test_is_valid_session_false_no_session(self):
        self.assertFalse(self.sessions.is_valid_session(self.email, self.token))

    def test_has_session_true(self):
        self.sessions.add_session(self.email, self.token, self.auth_type)
        self.assertTrue(self.sessions.has_session(self.email))

    def test_has_session_false(self):
        self.assertFalse(self.sessions.has_session(self.email))

    def test_thread_safety(self):
        import threading
        def worker():
            self.sessions.add_session(self.email, self.token, self.auth_type)
            self.assertTrue(self.sessions.has_session(self.email))
            self.sessions.delete_session(self.email)
            self.assertFalse(self.sessions.has_session(self.email))

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
