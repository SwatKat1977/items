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
import asyncio
import os
from quart import Quart
from application import Service

## Quart application instance
app = Quart(__name__)
service = Service(app)


async def cancel_background_tasks():
    """
    Cancel and await the application's background task, if it exists.

    This function looks for a task stored on the global ``app`` object
    under the attribute ``background_task``. If found, it cancels the task
    and safely awaits its termination. Any ``asyncio.CancelledError``
    raised during cancellation is suppressed.

    This is typically called during application shutdown to ensure that
    background operations are gracefully stopped.

    Raises:
        asyncio.CancelledError: Only if the cancellation is not suppressed
            (unexpected behavior).
    """
    task = getattr(app, "background_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.before_serving
async def startup() -> None:
    """
    Code executed before Quart has begun serving http requests.

    returns:
        None
    """
    if not await service.initialise():
        os._exit(1)

    app.background_task = asyncio.create_task(service.run())


@app.after_serving
async def shutdown() -> None:
    """
    Code executed after Quart has stopped serving http requests.

    returns:
        None
    """
    service.shutdown_event.set()

    if app is not None:
        await cancel_background_tasks()
    else:
        print("[WARN] app is None on shutdown, skipping cleanup")
