"""
Copyright 2025 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import threading

class ThreadSafeSingleton(type):
    """
    Implementation of a thread-safe singleton using a double-checked locking
    pattern.
    """
    _instances = {}
    _singleton_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):

        # double-checked locking pattern (https://en.wikipedia.org/wiki/Double-checked_locking)
        if cls not in cls._instances:
            with cls._singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(ThreadSafeSingleton, cls) \
                        .__call__(*args, **kwargs)

        return cls._instances[cls]
