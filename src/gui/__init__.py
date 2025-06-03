"""
GUI components with proper separation of concerns and dependency injection.
"""

from .main_window import MainWindow
from .camera_widget import CameraWidget
from .speech_widget import SpeechWidget

__all__ = ["MainWindow", "CameraWidget", "SpeechWidget"]
