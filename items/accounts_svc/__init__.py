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
import sys
from quart import Quart
from application import Application

# Quart application instance
app = Quart(__name__)

application = Application(app)

test

@app.before_serving
async def startup() -> None:
    """
    Code executed before Quart has began serving http requests.

    returns:
        None
    """
    app.service_task = asyncio.ensure_future(application.run())

@app.after_serving
async def shutdown() -> None:
    """
    Code executed after Quart has stopped serving http requests.

    returns:
        None
    """
    application.stop()

if not application.initialise():
    sys.exit()
