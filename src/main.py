#!/usr/bin/env python3
"""
Camera Application Entry Point
"""

import sys
from PyQt5.QtWidgets import QApplication

from camera_app import CameraApp


def main():
    """Main entry point for the camera application."""
    app = QApplication(sys.argv)

    try:
        camera_app = CameraApp()
        camera_app.show()
        return app.exec()
    except Exception as e:
        print(f"Error starting camera application: {e}")
        return 1
    finally:
        # Cleanup is handled in CameraApp destructor
        pass


if __name__ == "__main__":
    sys.exit(main())
