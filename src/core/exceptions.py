"""
Custom exceptions for the application.
"""


class AppBaseException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class CameraException(AppBaseException):
    """Camera-related exceptions."""

    pass


class CameraInitializationError(CameraException):
    """Raised when camera initialization fails."""

    pass


class CameraCaptureError(CameraException):
    """Raised when camera capture fails."""

    pass


class SpeechException(AppBaseException):
    """Speech recognition-related exceptions."""

    pass


class SpeechInitializationError(SpeechException):
    """Raised when speech service initialization fails."""

    pass


class SpeechRecognitionError(SpeechException):
    """Raised when speech recognition fails."""

    pass


class AudioDeviceError(SpeechException):
    """Raised when audio device operations fail."""

    pass


class ConfigurationException(AppBaseException):
    """Configuration-related exceptions."""

    pass


class FileOperationException(AppBaseException):
    """File operation-related exceptions."""

    pass
