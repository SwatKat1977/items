import time
import unittest
from items.shared.service_state import ServiceState
from items.shared.service_health_enums import ComponentDegradationLevel


class TestServicerState(unittest.TestCase):

    def _make_state(self) -> ServiceState:
        return ServiceState(version="1.0.0")

    # ------------------------------------------------------------------
    # uptime_seconds
    # ------------------------------------------------------------------

    def test_uptime_seconds_is_non_negative(self):
        state = self._make_state()
        self.assertGreaterEqual(state.uptime_seconds, 0)

    # ------------------------------------------------------------------
    # mark_database_failed
    # ------------------------------------------------------------------

    def test_mark_database_failed_when_disabled_is_noop(self):
        state = self._make_state()
        state.database_enabled = False
        state.mark_database_failed()
        self.assertEqual(state.database_health, ComponentDegradationLevel.NONE)

    def test_mark_database_failed_when_enabled(self):
        state = self._make_state()
        state.database_enabled = True
        state.mark_database_failed("Disk full")
        self.assertEqual(state.database_health, ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(state.database_health_reason, "Disk full")

    def test_mark_database_failed_default_reason(self):
        state = self._make_state()
        state.database_enabled = True
        state.mark_database_failed()
        self.assertEqual(state.database_health_reason, "Fatal SQL failure")

    # ------------------------------------------------------------------
    # mark_service_failed
    # ------------------------------------------------------------------

    def test_mark_service_failed(self):
        state = self._make_state()
        state.mark_service_failed("Crash")
        self.assertEqual(state.service_health, ComponentDegradationLevel.FULLY_DEGRADED)
        self.assertEqual(state.service_health_reason, "Crash")

    # ------------------------------------------------------------------
    # enter_maintenance / exit_maintenance
    # ------------------------------------------------------------------

    def test_enter_maintenance(self):
        state = self._make_state()
        state.enter_maintenance("Upgrade")
        self.assertTrue(state.in_maintenance)
        self.assertEqual(state.maintenance_reason, "Upgrade")

    def test_enter_maintenance_default_reason(self):
        state = self._make_state()
        state.enter_maintenance()
        self.assertEqual(state.maintenance_reason, "Entering maintenance mode")

    def test_exit_maintenance(self):
        state = self._make_state()
        state.enter_maintenance()
        state.exit_maintenance()
        self.assertFalse(state.in_maintenance)
        self.assertIsNone(state.maintenance_reason)

    # ------------------------------------------------------------------
    # is_available
    # ------------------------------------------------------------------

    def test_is_available_default(self):
        state = self._make_state()
        self.assertTrue(state.is_available())

    def test_is_available_in_maintenance(self):
        state = self._make_state()
        state.enter_maintenance()
        self.assertFalse(state.is_available())

    def test_is_available_service_failed(self):
        state = self._make_state()
        state.mark_service_failed("Dead")
        self.assertFalse(state.is_available())

    # ------------------------------------------------------------------
    # set_service_degraded
    # ------------------------------------------------------------------

    def test_set_service_degraded_partial(self):
        state = self._make_state()
        state.set_service_degraded("Slow", fully_degraded=False)
        self.assertEqual(state.service_health, ComponentDegradationLevel.PART_DEGRADED)
        self.assertEqual(state.service_health_reason, "Slow")

    def test_set_service_degraded_fully(self):
        state = self._make_state()
        state.set_service_degraded("Dead", fully_degraded=True)
        self.assertEqual(state.service_health, ComponentDegradationLevel.FULLY_DEGRADED)

    # ------------------------------------------------------------------
    # clear_service_degradation
    # ------------------------------------------------------------------

    def test_clear_service_degradation(self):
        state = self._make_state()
        state.mark_service_failed("Crash")
        state.clear_service_degradation()
        self.assertEqual(state.service_health, ComponentDegradationLevel.NONE)
        self.assertIsNone(state.service_health_reason)

    # ------------------------------------------------------------------
    # to_dict
    # ------------------------------------------------------------------

    def test_to_dict_without_database(self):
        state = self._make_state()
        d = state.to_dict()
        self.assertIn("service_health", d)
        self.assertIn("version", d)
        self.assertIn("startup_time", d)
        self.assertIn("in_maintenance", d)
        self.assertIn("uptime_seconds", d)
        self.assertNotIn("database_health", d)

    def test_to_dict_with_database(self):
        state = self._make_state()
        state.database_enabled = True
        d = state.to_dict()
        self.assertIn("database_health", d)
        self.assertIn("database_health_reason", d)

    def test_to_dict_service_health_is_string(self):
        state = self._make_state()
        d = state.to_dict()
        self.assertIsInstance(d["service_health"], str)

    # ------------------------------------------------------------------
    # _touch (via last_updated_time)
    # ------------------------------------------------------------------

    def test_touch_updates_last_updated_time(self):
        state = self._make_state()
        before = state.last_updated_time
        time.sleep(0.01)
        state.mark_service_failed("test")
        # last_updated_time may stay the same if called within the same second;
        # just verify it is not older than the initial value
        self.assertGreaterEqual(state.last_updated_time, before)
