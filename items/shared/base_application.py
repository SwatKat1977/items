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
import logging


class BaseApplication:
    """ Application framework class. """
    __slots__ = ["_is_initialised", "_logger", "_shutdown_requested"]

    @property
    def logger(self) -> logging.Logger:
        """
        Property getter for logger instance.

        returns:
            Returns the logger instance.
        """
        return self._logger

    @logger.setter
    def logger(self, logger : logging.Logger) -> None:
        """
        Property setter for logger instance.

        parameters:
            logger (logging.Logger) : Logger instance.
        """
        self._logger = logger

    def __init__(self):
        self._is_initialised : bool = False
        self._logger : logging.Logger = None
        self._shutdown_requested : bool = False

    def initialise(self) -> bool:
        """
        Application initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful), upon success
        self._is_initialised is set to True.

        returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        if self._initialise() is True:
            self._is_initialised = True
            init_status = True

        else:
            init_status = False

        return init_status

    async def run(self) -> None:
        """
        Start the application.
        """

        while not self._shutdown_requested and self._is_initialised:
            try:
                await self._main_loop()
                await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                break

        self._logger.info("Exiting application entrypoint...")

    def stop(self) -> None:
        """
        Stop the application, it will wait until shutdown has been marked as
        completed before calling the shutdown method.
        """

        self._logger.info("Stopping application...")
        self._logger.info('Waiting for application shutdown to complete')

        self._shutdown_requested = True


        self._shutdown()

    def _initialise(self) -> bool:
        """
        Application initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful).

        returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        return True

    async def _main_loop(self) -> None:
        """ Abstract method for main application. """
        raise NotImplementedError("Requires implementing")

    async def _shutdown(self) -> None:
        """ Abstract method for application shutdown. """
