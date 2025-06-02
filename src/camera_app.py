"""
Camera Application GUI and Logic
"""

from PyQt5 import QtCore
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from libcamera import controls

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2

from camera_config import CameraConfig
from file_utils import FileManager


class CameraApp(QWidget):
    """Main camera application window."""

    # Application states
    STATE_AF = 0
    STATE_CAPTURE = 1

    def __init__(self):
        super().__init__()
        self.state = self.STATE_AF
        self.picam2 = None
        self.qpicamera2 = None
        self.file_manager = FileManager()

        self._init_camera()
        self._init_ui()

    def _init_camera(self):
        """Initialize the camera with configuration."""
        self.picam2 = Picamera2()

        # Check autofocus support
        if "AfMode" not in self.picam2.camera_controls:
            raise RuntimeError("Attached camera does not support autofocus")

        # Configure camera
        config = CameraConfig.get_preview_config(self.picam2)
        self.picam2.configure(config)
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})

    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Qt Picamera2 App")

        # Get preview dimensions
        preview_width, preview_height = CameraConfig.get_preview_size(self.picam2)

        # Create camera preview widget
        bg_colour = self.palette().color(QPalette.Background).getRgb()[:3]
        self.qpicamera2 = QGlPicamera2(
            self.picam2, width=preview_width, height=preview_height, bg_colour=bg_colour
        )
        self.qpicamera2.done_signal.connect(
            self._camera_callback, type=QtCore.Qt.QueuedConnection
        )

        # Create controls
        self._create_controls()

        # Layout
        self._setup_layout(preview_width, preview_height)

    def _create_controls(self):
        """Create UI controls."""
        self.button = QPushButton("Click to capture JPEG")
        self.button.clicked.connect(self._on_capture_clicked)

        self.af_checkbox = QCheckBox("AF before capture", checked=False)

        self.continuous_checkbox = QCheckBox("Continuous AF", checked=False)
        self.continuous_checkbox.toggled.connect(self._on_continuous_toggled)

    def _setup_layout(self, preview_width, preview_height):
        """Setup the window layout."""
        layout_v_main = QVBoxLayout()
        layout_h_controls = QHBoxLayout()

        # Add preview to main layout
        layout_v_main.addWidget(self.qpicamera2)

        # Add controls to horizontal layout
        layout_h_controls.addWidget(self.continuous_checkbox)
        layout_h_controls.addWidget(self.af_checkbox)
        layout_h_controls.addWidget(self.button)

        # Add controls to main layout
        layout_v_main.addLayout(layout_h_controls)

        # Set window properties
        self.resize(preview_width, preview_height + 80)
        self.setLayout(layout_v_main)

    def _on_capture_clicked(self):
        """Handle capture button click."""
        self._set_controls_enabled(False)

        self.state = (
            self.STATE_AF if self.af_checkbox.isChecked() else self.STATE_CAPTURE
        )

        if self.state == self.STATE_AF:
            self.picam2.autofocus_cycle(signal_function=self.qpicamera2.signal_done)
        else:
            self._do_capture()

    def _do_capture(self):
        """Perform image capture."""
        cfg = self.picam2.create_still_configuration()
        filename = self.file_manager.get_next_filename("output")
        self.picam2.switch_mode_and_capture_file(
            cfg, filename, signal_function=self.qpicamera2.signal_done
        )

    def _camera_callback(self, job):
        """Handle camera operation completion."""
        if self.state == self.STATE_AF:
            self.state = self.STATE_CAPTURE
            success = "succeeded" if self.picam2.wait(job) else "failed"
            print(f"AF cycle {success} in {job.calls} frames")
            self._do_capture()
        else:
            self.picam2.wait(job)

            # Show capture result
            latest_file = self.file_manager.get_latest_filename("output")
            if latest_file:
                print(f"Captured: {latest_file}")

            # Reset camera and UI
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            self._set_controls_enabled(True)

    def _on_continuous_toggled(self, checked):
        """Handle continuous autofocus toggle."""
        mode = controls.AfModeEnum.Continuous if checked else controls.AfModeEnum.Auto
        self.picam2.set_controls({"AfMode": mode})

    def _set_controls_enabled(self, enabled):
        """Enable or disable UI controls."""
        self.button.setEnabled(enabled)
        self.continuous_checkbox.setEnabled(enabled)
        self.af_checkbox.setEnabled(enabled)

    def show(self):
        """Show the window and start camera."""
        self.picam2.start()
        super().show()

    def closeEvent(self, event):
        """Handle window close event."""
        if self.picam2:
            self.picam2.stop()
        event.accept()
