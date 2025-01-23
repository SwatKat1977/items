import unittest
from threading import Thread
from thread_safe_singleton import ThreadSafeSingleton


class SingletonClass(metaclass=ThreadSafeSingleton):
    def __init__(self, value):
        self.value = value


class TestThreadSafeSingleton(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instances for each test
        ThreadSafeSingleton._instances = {}

    def test_single_instance(self):
        """Test that only one instance is created."""
        instance1 = SingletonClass("first")
        instance2 = SingletonClass("second")

        self.assertIs(instance1, instance2)
        self.assertEqual(instance1.value, "first")
        self.assertEqual(instance2.value, "first")

    def test_thread_safety(self):
        """Test that the singleton is thread-safe."""
        results = []

        def create_instance(value):
            instance = SingletonClass(value)
            results.append(instance)

        # Start multiple threads
        threads = [Thread(target=create_instance, args=(f"value-{i}",)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Ensure all threads returned the same instance
        self.assertTrue(all(instance is results[0] for instance in results))
        self.assertEqual(results[0].value, "value-0")

    def test_no_duplicate_instances(self):
        """Test that no duplicate instances are created."""
        instance1 = SingletonClass("test")
        instance2 = SingletonClass("test")
        self.assertIs(instance1, instance2)

    def test_instances_are_reset(self):
        """Test that resetting the instances clears the singleton state."""
        instance1 = SingletonClass("initial")
        ThreadSafeSingleton._instances = {}
        instance2 = SingletonClass("reset")

        self.assertIsNot(instance1, instance2)
        self.assertEqual(instance2.value, "reset")
