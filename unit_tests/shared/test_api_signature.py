import unittest
from items.shared.api_signature import verify_api_signature, generate_api_signature


class TestApiSignature(unittest.TestCase):

    SECRET_KEY = b"test-secret-key"

    # ------------------------------------------------------------------
    # generate_api_signature
    # ------------------------------------------------------------------

    def test_generate_with_bytes(self):
        sig = generate_api_signature(self.SECRET_KEY, b"hello")
        self.assertIsInstance(sig, str)
        self.assertTrue(len(sig) > 0)

    def test_generate_with_str(self):
        sig = generate_api_signature(self.SECRET_KEY, "hello")
        self.assertIsInstance(sig, str)
        self.assertEqual(sig, generate_api_signature(self.SECRET_KEY, b"hello"))

    def test_generate_with_dict(self):
        sig = generate_api_signature(self.SECRET_KEY, {"key": "value"})
        self.assertIsInstance(sig, str)
        self.assertTrue(len(sig) > 0)

    def test_generate_dict_is_deterministic(self):
        data = {"b": 2, "a": 1}
        sig1 = generate_api_signature(self.SECRET_KEY, data)
        sig2 = generate_api_signature(self.SECRET_KEY, data)
        self.assertEqual(sig1, sig2)

    def test_generate_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            generate_api_signature(self.SECRET_KEY, 12345)

    # ------------------------------------------------------------------
    # verify_api_signature
    # ------------------------------------------------------------------

    def test_verify_with_bytes(self):
        sig = generate_api_signature(self.SECRET_KEY, b"hello")
        self.assertTrue(verify_api_signature(self.SECRET_KEY, b"hello", sig))

    def test_verify_with_str(self):
        sig = generate_api_signature(self.SECRET_KEY, "hello")
        self.assertTrue(verify_api_signature(self.SECRET_KEY, "hello", sig))

    def test_verify_with_dict(self):
        data = {"key": "value"}
        sig = generate_api_signature(self.SECRET_KEY, data)
        self.assertTrue(verify_api_signature(self.SECRET_KEY, data, sig))

    def test_verify_wrong_signature_returns_false(self):
        sig = generate_api_signature(self.SECRET_KEY, b"hello")
        self.assertFalse(verify_api_signature(self.SECRET_KEY, b"world", sig))

    def test_verify_invalid_type_raises(self):
        sig = generate_api_signature(self.SECRET_KEY, b"hello")
        with self.assertRaises(TypeError):
            verify_api_signature(self.SECRET_KEY, 99, sig)

    def test_generate_and_verify_roundtrip(self):
        data = {"user": "paul", "action": "login"}
        sig = generate_api_signature(self.SECRET_KEY, data)
        self.assertTrue(verify_api_signature(self.SECRET_KEY, data, sig))
