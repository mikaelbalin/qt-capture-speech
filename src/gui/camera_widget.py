import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import logging

from ..core.interfaces import CameraServiceInterface, FileManagerInterface


class CameraWidget(QWidget):
    """Camera widget with proper separation from business logic."""

    def __init__(
        self,
        camera_service: CameraServiceInterface,
        file_manager: FileManagerInterface,
        parent=None,
    ):
        super().__init__(parent)
        self.camera_service = camera_service
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)

        self.current_frame: np.ndarray = None
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout()

        # Camera display
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("border: 1px solid black;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_label)

        # Controls
        controls_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.capture_button = QPushButton("Capture Photo")

        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.capture_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Status
        self.status_label = QLabel("Camera: Stopped")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def connect_signals(self):
        """Connect signals and slots."""
        # Button signals
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.capture_button.clicked.connect(self.capture_photo)

        # Camera service signals
        self.camera_service.frame_captured.connect(self.update_frame)
        self.camera_service.error_occurred.connect(self.handle_error)
        self.camera_service.camera_status_changed.connect(self.update_status)

    def start_camera(self):
        """Start camera capture."""
        try:
            if self.camera_service.start_capture():
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.capture_button.setEnabled(True)
                self.status_label.setText("Camera: Starting...")
            else:
                self.show_error("Failed to start camera")

        except Exception as e:
            self.logger.error(f"Error starting camera: {str(e)}")
            self.show_error(f"Camera error: {str(e)}")

    def stop_camera(self):
        """Stop camera capture."""
        try:
            self.camera_service.stop_capture()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.capture_button.setEnabled(False)
            self.status_label.setText("Camera: Stopped")

            # Clear display
            self.camera_label.clear()
            self.camera_label.setText("Camera Feed")

        except Exception as e:
            self.logger.error(f"Error stopping camera: {str(e)}")
            self.show_error(f"Error stopping camera: {str(e)}")

    def capture_photo(self):
        """Capture and save photo."""
        try:
            if self.current_frame is not None:
                filename = self.file_manager.generate_filename("photo", "jpg")
                filepath = self.file_manager.get_image_path(filename)

                if self.camera_service.save_frame(self.current_frame, filepath):
                    self.show_info(f"Photo saved: {filename}")
                else:
                    self.show_error("Failed to save photo")
            else:
                self.show_error("No frame available to capture")

        except Exception as e:
            self.logger.error(f"Error capturing photo: {str(e)}")
            self.show_error(f"Capture error: {str(e)}")

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame: np.ndarray):
        """Update camera display with new frame."""
        try:
            self.current_frame = frame.copy()

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width

            # Create QImage
            q_image = QImage(
                rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888
            )

            # Scale to fit label
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            self.camera_label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.logger.error(f"Error updating frame: {str(e)}")

    @pyqtSlot(str)
    def handle_error(self, error_message: str):
        """Handle camera service errors."""
        self.show_error(error_message)

        # Reset UI state on error
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.status_label.setText("Camera: Error")

    @pyqtSlot(bool)
    def update_status(self, is_active: bool):
        """Update camera status."""
        if is_active:
            self.status_label.setText("Camera: Active")
        else:
            self.status_label.setText("Camera: Inactive")

    def show_error(self, message: str):
        """Show error message to user."""
        QMessageBox.critical(self, "Camera Error", message)

    def show_info(self, message: str):
        """Show info message to user."""
        QMessageBox.information(self, "Camera Info", message)

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.camera_service.cleanup()
        except Exception as e:
            self.logger.error(f"Error during camera widget cleanup: {str(e)}")
