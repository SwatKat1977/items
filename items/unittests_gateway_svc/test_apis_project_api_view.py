import unittest


class TestApiProjectApiView(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_sessions = MagicMock(spec=Sessions)
        self.view = HandshakeApiView(self.mock_logger, self.mock_sessions)

        # Set up Quart test client and mock dependencies.
        self.app = Quart(__name__)
        self.client = self.app.test_client()
