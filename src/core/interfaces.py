from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np


class CameraServiceInterface(QObject, ABC):
    """Abstract interface for camera service."""

    # Signals
    frame_captured = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    camera_status_changed = pyqtSignal(bool)

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize camera service."""
        pass

    @abstractmethod
    def start_capture(self) -> bool:
        """Start camera capture."""
        pass

    @abstractmethod
    def stop_capture(self) -> None:
        """Stop camera capture."""
        pass

    @abstractmethod
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame."""
        pass

    @abstractmethod
    def save_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Save frame to file."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass


class SpeechServiceInterface(QObject, ABC):
    """Abstract interface for speech recognition service."""

    # Signals
    transcription_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    recording_status_changed = pyqtSignal(bool)

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize speech service."""
        pass

    @abstractmethod
    def start_recognition(self) -> bool:
        """Start speech recognition."""
        pass

    @abstractmethod
    def stop_recognition(self) -> None:
        """Stop speech recognition."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources."""
        pass


class FileManagerInterface(ABC):
    """Abstract interface for file management."""

    @abstractmethod
    def generate_filename(self, prefix: str = "capture", extension: str = "jpg") -> str:
        """Generate unique filename."""
        pass

    @abstractmethod
    def ensure_directory(self, path: str) -> bool:
        """Ensure directory exists."""
        pass

    @abstractmethod
    def save_file(self, data: Any, filepath: str) -> bool:
        """Save data to file."""
        pass


class ConfigManagerInterface(ABC):
    """Abstract interface for configuration management."""

    @abstractmethod
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
