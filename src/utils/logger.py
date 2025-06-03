import logging
import logging.handlers
import os
from typing import Optional

from ..core.interfaces import ConfigManagerInterface


class LoggerConfig:
    """Logger configuration utility."""

    def __init__(self, config_manager: ConfigManagerInterface):
        self.config = config_manager
        self._configured = False

    def setup_logging(self) -> None:
        """Setup application logging configuration."""
        if self._configured:
            return

        # Get configuration
        log_level = self.config.get("logging.level", "INFO")
        log_format = self.config.get(
            "logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        log_file = self.config.get("logging.file", "app.log")
        max_size_mb = self.config.get("logging.max_size_mb", 10)
        backup_count = self.config.get("logging.backup_count", 5)

        # Create formatter
        formatter = logging.Formatter(log_format)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)

        # File handler with rotation
        if log_file:
            try:
                # Ensure log directory exists
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
                    backupCount=backup_count,
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(getattr(logging, log_level.upper()))
                root_logger.addHandler(file_handler)

            except Exception as e:
                # If file logging fails, log to console
                root_logger.error(f"Failed to setup file logging: {str(e)}")

        self._configured = True
        root_logger.info("Logging configuration completed")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get logger instance."""
        return logging.getLogger(name)

    def set_log_level(self, level: str) -> None:
        """Dynamically change log level."""
        try:
            log_level = getattr(logging, level.upper())
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)

            # Update all handlers
            for handler in root_logger.handlers:
                handler.setLevel(log_level)

        except AttributeError:
            raise ValueError(f"Invalid log level: {level}")
