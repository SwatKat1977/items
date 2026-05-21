from weaver_framework.configuration_system.configuration_manager import (
    ConfigurationManager)
from items.services.items_identity.configuration_layout import ConfigurationConstants


class IdentityConfiguration(ConfigurationManager):
    """Configuration manager for the identity service.

    This class provides strongly-typed accessors for configuration
    values used by the identity service. Configuration entries are
    retrieved through the underlying ``ConfigurationManager`` base
    class.

    Properties:
        logging_log_level: Logging level used by the identity service.
        backend_db_filename: Filename or path of the backend database.
    """

    @property
    def logging_log_level(self) -> str:
        """Return the configured logging level.

        Returns:
            The configured logging level value.
        """
        return self.get_entry(ConfigurationConstants.SECTION_LOGGING,
                              ConfigurationConstants.ITEM_LOGGING_LOG_LEVEL)

    @property
    def backend_db_filename(self) -> str:
        """Return the backend database filename.

        Returns:
            The configured backend database filename or path.
        """
        return self.get_entry(ConfigurationConstants.SECTION_BACKEND,
                              ConfigurationConstants.ITEM_BACKEND_DB_FILENAME)
