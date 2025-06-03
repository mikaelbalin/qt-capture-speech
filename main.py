#!/usr/bin/env python3
"""
Qt Camera and Speech Recognition Application - Main Entry Point
Refactored version with proper architecture and dependency injection.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.config import ConfigManager
from src.core.container import DIContainer
from src.core.interfaces import (
    CameraServiceInterface,
    SpeechServiceInterface,
    FileManagerInterface,
    ConfigManagerInterface,
)
from src.camera import CameraService
from src.speech import SpeechService
from src.utils import FileManager, LoggerConfig
from src.gui import MainWindow


class Application:
    """Main application class with proper lifecycle management."""

    def __init__(self):
        self.qt_app = None
        self.main_window = None
        self.container = DIContainer()
        self.config = None

    def initialize(self) -> bool:
        """Initialize application components."""
        try:
            # Load configuration
            config_path = Path(__file__).parent / "config" / "app_config.yaml"
            self.config = ConfigManager()
            self.config.load_config(str(config_path))

            # Setup logging
            logger_config = LoggerConfig(self.config)
            logger_config.setup_logging()

            # Register services in DI container
            self._register_services()

            # Create Qt application
            self.qt_app = QApplication(sys.argv)
            self.qt_app.setApplicationName(
                self.config.get("app.name", "Qt Camera Speech")
            )
            self.qt_app.setApplicationVersion(self.config.get("app.version", "2.0.0"))

            return True

        except Exception as e:
            print(f"Application initialization failed: {str(e)}")
            return False

    def _register_services(self):
        """Register services in dependency injection container."""
        # Register config manager
        self.container.register_instance(ConfigManagerInterface, self.config)

        # Register file manager
        self.container.register_singleton(
            FileManagerInterface, FileManager, self.config
        )

        # Register camera service
        self.container.register_singleton(
            CameraServiceInterface, CameraService, self.config
        )

        # Register speech service
        self.container.register_singleton(
            SpeechServiceInterface, SpeechService, self.config
        )

    def run(self) -> int:
        """Run the application."""
        try:
            if not self.initialize():
                return 1

            # Create main window
            self.main_window = MainWindow(self.container, self.config)
            self.main_window.show()

            # Run Qt event loop
            return self.qt_app.exec_()

        except KeyboardInterrupt:
            print("\nApplication interrupted by user")
            return 0
        except Exception as e:
            print(f"Application error: {str(e)}")
            return 1
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup application resources."""
        try:
            if self.container:
                self.container.clear()
        except Exception as e:
            print(f"Cleanup error: {str(e)}")


def main():
    """Main entry point."""
    app = Application()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
