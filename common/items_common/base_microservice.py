"""
Copyright (C) 2025  Integrated Test Management Suite Development Team
SPDX-License-Identifier: AGPL-3.0-or-later

This file is part of Integrated Test Management Suite. See the LICENSE
file in the project root for full license details.
"""
import abc
import asyncio
import logging
import os
import typing
from items_common import __version__
from items_common.service_state import ServiceState

class BaseMicroservice(abc.ABC):
    """ Base microservice class. """
    __slots__ = ["_is_initialised", "_logger", "_shutdown_complete",
                 "_shutdown_event", "_service_state"]

    BOOL_TRUE_VALUES: set = {"1", "true", "yes", "on"}
    BOOL_FALSE_VALUES: set = {"0", "false", "no", "off"}

    def __init__(self):
        self._is_initialised: bool = False
        self._logger: typing.Optional[logging.Logger] = None
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._shutdown_complete: asyncio.Event = asyncio.Event()
        self._service_state: ServiceState = ServiceState(version=__version__)

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

    @property
    def shutdown_event(self) -> asyncio.Event:
        """
        Event used to signal the shutdown of the service.

        This event should be awaited or checked by background tasks to
        gracefully stop operations when the application is shutting down.
        """
        return self._shutdown_event

    @property
    def shutdown_complete(self) -> asyncio.Event:
        """
        Event that indicates the service has completed its shutdown process.

        This should be set when all shutdown tasks and cleanup procedures have
        finished, allowing other components (like the main app) to know when
        it's safe to exit.
        """
        return self._shutdown_complete

    async def initialise(self) -> bool:
        """
        Microservice initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful), upon success
        self._is_initialised is set to True.

        Returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        if await self._initialise():
            self._is_initialised = True
            return True

        await self.stop()

        return False

    async def run(self) -> None:
        """
        Start the microservice.
        """

        if not self._is_initialised:
            self._logger.warning("Microservice is not initialised. Exiting run loop.")
            return

        self._logger.info("Microservice starting main loop.")

        try:
            while True:
                if self.shutdown_event.is_set():
                    break

                await self._main_loop()
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            self._logger.debug("Service: Keyboard interrupt received.")
            self._shutdown_event.set()

        except asyncio.CancelledError:
            self._logger.debug("Service: Cancellation received.")
            raise

        finally:
            self._logger.info("Exiting microservice run loop...")
            await self.stop()
            self._logger.info("Shutdown complete.")

    async def stop(self) -> None:
        """
        Stop the microservice, it will wait until shutdown has been marked as
        completed before calling the shutdown method.
        """

        self._logger.info("Stopping microservice...")
        self._logger.info('Waiting for microservice shutdown to complete')

        self._shutdown_event.set()

        await self._shutdown()
        self._shutdown_complete.set()

        self._logger.info('Microservice shutdown complete...')

    async def _initialise(self) -> bool:
        """
        Microservice initialisation.  It should return a boolean
        (True => Successful, False => Unsuccessful).

        Returns:
            Boolean: True => Successful, False => Unsuccessful.
        """
        return True

    @abc.abstractmethod
    async def _main_loop(self) -> None:
        """ Abstract method for main microservice loop. """

    @abc.abstractmethod
    async def _shutdown(self):
        """ Abstract method for microservice shutdown. """

    def _check_for_configuration(self,
                                 config_file_env: str,
                                 config_file_required_env: str):
        """
        Check whether a configuration file is required and available based
        on environment variables.

        This function inspects two environment variables:
          - One specifying the path to a configuration file.
          - One specifying whether the configuration file is required.

        It validates the "required" flag against known boolean true/false
        values, determines whether the configuration file is missing when
        required, and returns the appropriate error status and state.

        Args:
            config_file_env (str):
                The name of the environment variable that holds the
                configuration file path.
            config_file_required_env (str):
                The name of the environment variable that indicates whether the
                configuration file is required.
                Expected values (case-insensitive):
                "true", "1", "yes", "on", "false", "0", "no", "off".

        Returns:
            tuple[str | None, bool, str | None]:
                A tuple containing:
                - `error_status` (str | None): An error message if a fatal
                  error occurred, otherwise None.
                - `config_file_required` (bool): Whether a configuration file
                  is required.
                - `config_file` (str | None): The configuration file path if
                  defined, otherwise None.

        Notes:
            - If `config_file_required_env` contains an invalid value, an error
              message is returned.
            - If a configuration file is required but not provided, an error
              message is returned.
            - If both checks pass, `error_status` will be None.

        Example:
            >>> os.environ["MY_CONFIG_FILE"] = "/etc/app.conf"
            >>> os.environ["MY_CONFIG_FILE_REQUIRED"] = "true"
            >>> self._check_for_configuration("MY_CONFIG_FILE",
                                              "MY_CONFIG_FILE_REQUIRED")
            (None, True, "/etc/app.conf")
        """
        # Default return values
        config_file_required: bool = False
        error_status: typing.Optional[str] = None

        config_file = os.getenv(config_file_env, None)
        raw_required = os.getenv(config_file_required_env,
                                 "false").strip().lower()

        # Check if it's a true value.
        if raw_required in self.BOOL_TRUE_VALUES:
            config_file_required = True

        # Check if it's a false value.
        elif raw_required in self.BOOL_FALSE_VALUES:
            config_file_required = False

        # Unknown value - e.g. not true or false value.
        else:
            error_status = (f"Invalid value for {config_file_required_env}: "
                            f"'{raw_required}'")

        if not error_status and not config_file and config_file_required:
            error_status = "Configuration file is not defined"

        return error_status, config_file_required, config_file
