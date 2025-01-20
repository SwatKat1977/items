import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import logging
from base_application import BaseApplication

class TestableBaseApplication(BaseApplication):
    def _initialise(self) -> bool:
        return super()._initialise()

    async def _main_loop(self) -> None:
        pass

    def _shutdown(self) -> None:
        pass

class TestBaseApplication(unittest.TestCase):
    def setUp(self):
        self.app = TestableBaseApplication()
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.app.logger = self.mock_logger

    def test_initialise_success(self):
        self.app._initialise = MagicMock(return_value=True)  # Mock the _initialise method
        self.assertTrue(self.app.initialise())
        self.assertTrue(self.app._is_initialised)
        self.app._initialise.assert_called_once()

    def test_initialise_failure(self):
        self.app._initialise = MagicMock(return_value=False)  # Mock the _initialise method
        self.assertFalse(self.app.initialise())
        self.assertFalse(self.app._is_initialised)
        self.app._initialise.assert_called_once()

    @patch("asyncio.sleep", new_callable=AsyncMock)
    def test_run(self, mock_sleep):
        # Set up application state
        self.app._is_initialised = True
        self.app._shutdown_requested = False

        # Mock `_main_loop` to simulate one loop iteration before stopping
        self.app._main_loop = AsyncMock(side_effect=[None, KeyboardInterrupt()])  # Simulate loop and exit

        # Use a real logger for `assertLogs`
        real_logger = logging.getLogger("root")
        real_logger.setLevel(logging.INFO)
        self.app.logger = real_logger

        # Assert log output and run the application
        with self.assertLogs("root", level="INFO") as log:
            asyncio.run(self.app.run())
            self.assertIn("INFO:root:Exiting application entrypoint...", log.output)

        # Verify `_main_loop` was called twice
        self.assertEqual(self.app._main_loop.call_count, 2)

    def test_stop(self):
        self.app._shutdown = MagicMock()  # Mock the _shutdown method
        self.app.stop()

        self.assertTrue(self.app._shutdown_requested)
        self.app._shutdown.assert_called_once()
        self.mock_logger.info.assert_any_call("Stopping application...")
        self.mock_logger.info.assert_any_call("Waiting for application shutdown to complete")

    def test_logger_property(self):
        new_logger = MagicMock(spec=logging.Logger)
        self.app.logger = new_logger
        self.assertEqual(self.app.logger, new_logger)

    """
    def test_main_loop_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.app._main_loop())

    def test_shutdown_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.app._shutdown()
    """
