import cv2
import numpy as np
import logging
from typing import Optional
from PyQt5.QtCore import QTimer, pyqtSignal
from contextlib import contextmanager

from ..core.interfaces import CameraServiceInterface, ConfigManagerInterface
from ..core.exceptions import CameraInitializationError, CameraCaptureError


class CameraService(CameraServiceInterface):
    """Enhanced camera service with async operations and proper resource management."""

    def __init__(self, config_manager: ConfigManagerInterface):
        super().__init__()
        self.config = config_manager
        self.logger = logging.getLogger(__name__)

        # Camera properties
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_initialized = False
        self.is_capturing = False

        # Configuration
        self.device_id = self.config.get("camera.device_id", 0)
        self.width = self.config.get("camera.width", 640)
        self.height = self.config.get("camera.height", 480)
        self.fps = self.config.get("camera.fps", 30)
        self.save_quality = self.config.get("camera.save_quality", 95)

        # Timer for continuous capture
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self._capture_frame_async)

    def initialize(self) -> bool:
        """Initialize camera with error handling."""
        try:
            if self.is_initialized:
                self.logger.warning("Camera already initialized")
                return True

            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                raise CameraInitializationError(
                    f"Cannot open camera device {self.device_id}"
                )

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            self.logger.info(
                f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps"
            )

            self.is_initialized = True
            self.camera_status_changed.emit(True)
            return True

        except Exception as e:
            error_msg = f"Camera initialization failed: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.cleanup()
            return False

    def start_capture(self) -> bool:
        """Start continuous camera capture."""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return False

            if self.is_capturing:
                self.logger.warning("Camera already capturing")
                return True

            # Start capture timer
            interval = max(1, int(1000 / self.fps))  # Convert fps to milliseconds
            self.capture_timer.start(interval)
            self.is_capturing = True

            self.logger.info("Camera capture started")
            return True

        except Exception as e:
            error_msg = f"Failed to start camera capture: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def stop_capture(self) -> None:
        """Stop camera capture."""
        try:
            if self.capture_timer.isActive():
                self.capture_timer.stop()

            self.is_capturing = False
            self.logger.info("Camera capture stopped")

        except Exception as e:
            error_msg = f"Error stopping camera capture: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame synchronously."""
        try:
            if not self.is_initialized or not self.cap:
                raise CameraCaptureError("Camera not initialized")

            ret, frame = self.cap.read()
            if not ret or frame is None:
                raise CameraCaptureError("Failed to capture frame")

            return frame

        except Exception as e:
            error_msg = f"Frame capture failed: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def _capture_frame_async(self) -> None:
        """Internal method for async frame capture via timer."""
        frame = self.capture_frame()
        if frame is not None:
            self.frame_captured.emit(frame)

    def save_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Save frame to file with proper error handling."""
        try:
            if frame is None or frame.size == 0:
                raise CameraCaptureError("Invalid frame data")

            # Determine save parameters based on file extension
            ext = filename.lower().split(".")[-1]
            if ext in ["jpg", "jpeg"]:
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.save_quality]
            elif ext == "png":
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            else:
                encode_params = []

            success = cv2.imwrite(filename, frame, encode_params)
            if not success:
                raise CameraCaptureError(f"Failed to save frame to {filename}")

            self.logger.info(f"Frame saved to {filename}")
            return True

        except Exception as e:
            error_msg = f"Failed to save frame: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    @contextmanager
    def camera_context(self):
        """Context manager for safe camera operations."""
        initialized_here = False
        try:
            if not self.is_initialized:
                if self.initialize():
                    initialized_here = True
                else:
                    raise CameraInitializationError("Failed to initialize camera")

            yield self

        finally:
            if initialized_here:
                self.cleanup()

    def get_camera_info(self) -> dict:
        """Get current camera information."""
        if not self.is_initialized or not self.cap:
            return {}

        return {
            "device_id": self.device_id,
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "is_capturing": self.is_capturing,
            "backend": self.cap.getBackendName(),
        }

    def cleanup(self) -> None:
        """Cleanup camera resources."""
        try:
            self.stop_capture()

            if self.cap is not None:
                self.cap.release()
                self.cap = None

            self.is_initialized = False
            self.is_capturing = False
            self.camera_status_changed.emit(False)

            self.logger.info("Camera resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
