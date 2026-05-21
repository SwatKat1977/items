"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

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
import asyncio
import os
import signal
from hypercorn.asyncio import serve
from hypercorn.config import Config
from items.services.items_identity import app, service
# from veil.identity_service import app, service


async def main() -> int:
    """Run the identity service application.

    This function performs service initialization, starts the
    background service task, configures graceful shutdown signal
    handling, and launches the ASGI server.

    The service will:
        - Initialize required service components
        - Start the service runtime loop
        - Configure SIGINT and SIGTERM shutdown handlers
        - Start the Hypercorn ASGI server
        - Gracefully stop all running tasks during shutdown

    Returns:
        Exit status code.

        Returns:
            0: Service exited successfully.
            1: Service initialization failed.
    """
    if not await service.initialise():
        await service.stop()
        return 1

    service_task = asyncio.create_task(service.run())

    shutdown_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(
                sig,
                shutdown_event.set
            )
        except NotImplementedError:
            # Windows fallback; CTRL+C still cancels asyncio.run().
            pass

    host = os.getenv("ITEMS_IDENTITY_HOST", "127.0.0.1")
    port = int(os.getenv("ITEMS_IDENTITY_PORT", "5050"))

    config = Config()
    config.bind = [f"{host}:{port}"]

    server_task = asyncio.create_task(
        serve(app, config, shutdown_trigger=shutdown_event.wait)
    )

    try:
        await server_task
    except KeyboardInterrupt:
        shutdown_event.set()
    finally:
        await service.stop()

        service_task.cancel()
        await asyncio.gather(service_task, return_exceptions=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))

    except KeyboardInterrupt:
        pass
