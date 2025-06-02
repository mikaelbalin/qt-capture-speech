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
    QFrame,
    QDialog,
    QGridLayout,
    QSizePolicy,
    QLabel,
)
from PyQt5.QtCore import Qt
from libcamera import controls

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2

from camera_config import CameraConfig
from file_utils import FileManager
from speech_widget import SpeechRecognitionWidget


class CameraPreviewPopup(QDialog):
    """Popup window for camera preview."""

    def __init__(self, picam2, parent=None):
        super().__init__(parent)
        self.picam2 = picam2
        self.qpicamera2 = None
        self._init_ui()

    def _init_ui(self):
        """Initialize the popup UI."""
        self.setWindowTitle("Camera Preview")
        self.setModal(False)  # Allow interaction with main window

        # Make window resizable
        self.setMinimumSize(400, 300)
        self.setMaximumSize(1200, 900)

        # Create camera preview widget - let it use default size first
        bg_colour = self.palette().color(QPalette.Background).getRgb()[:3]
        self.qpicamera2 = QGlPicamera2(self.picam2, bg_colour=bg_colour)

        # Set size policy to allow expansion
        self.qpicamera2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.qpicamera2)
        self.setLayout(layout)

        # Set initial window size
        self.resize(800, 600)

    def closeEvent(self, event):
        """Handle close event."""
        self.hide()  # Hide instead of closing to keep the widget alive
        event.ignore()


class CameraApp(QWidget):
    """Main camera application window."""

    # Application states
    STATE_AF = 0
    STATE_CAPTURE = 1

    def __init__(self):
        super().__init__()
        self.state = self.STATE_AF
        self.picam2 = None
        self.preview_popup = None
        self.file_manager = FileManager()
        self.speech_widget = None

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
        self.setWindowTitle("Camera & Speech Recognition App")

        # Create camera preview popup
        self.preview_popup = CameraPreviewPopup(self.picam2, self)
        self.preview_popup.qpicamera2.done_signal.connect(
            self._camera_callback, type=QtCore.Qt.QueuedConnection
        )

        # Create main vertical layout
        main_layout = QVBoxLayout()

        # Create speech recognition widget (top section)
        self.speech_widget = SpeechRecognitionWidget()
        self.speech_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.speech_widget, 1)  # Takes most space

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #ccc; }")
        main_layout.addWidget(separator)

        # Create camera controls panel (bottom section)
        camera_panel = self._create_camera_controls_panel()
        camera_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout.addWidget(camera_panel, 0)  # Fixed size, doesn't expand

        self.setLayout(main_layout)

        # Set window size
        self.resize(600, 500)

    def _create_camera_controls_panel(self):
        """Create the camera controls panel widget."""
        camera_widget = QWidget()

        # Create camera controls
        self._create_camera_controls()

        # Camera controls in grid layout
        layout = QVBoxLayout()

        # Title label
        title_label = QLabel("Camera Controls")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin: 5px;")
        layout.addWidget(title_label)

        # Controls grid (2x3 grid)
        controls_grid = QGridLayout()

        # Row 0
        controls_grid.addWidget(self.continuous_checkbox, 0, 0, 1, 2)  # Span 2 columns
        controls_grid.addWidget(self.capture_button, 0, 2, 1, 2)  # Span 2 columns

        # Row 1
        controls_grid.addWidget(self.af_checkbox, 1, 0, 1, 2)  # Span 2 columns
        controls_grid.addWidget(self.preview_button, 1, 2, 1, 2)  # Span 2 columns

        layout.addLayout(controls_grid)

        camera_widget.setLayout(layout)
        return camera_widget

    def _create_camera_controls(self):
        """Create camera UI controls."""
        self.preview_button = QPushButton("Show Camera Preview")
        self.preview_button.setCheckable(True)
        self.preview_button.clicked.connect(self._on_preview_toggle)

        self.capture_button = QPushButton("Click to capture JPEG")
        self.capture_button.clicked.connect(self._on_capture_clicked)

        self.af_checkbox = QCheckBox("AF before capture", checked=False)

        self.continuous_checkbox = QCheckBox("Continuous AF", checked=False)
        self.continuous_checkbox.toggled.connect(self._on_continuous_toggled)

    def _on_preview_toggle(self, checked):
        """Handle preview toggle button."""
        if checked:
            self.preview_popup.show()
            self.preview_button.setText("Hide Camera Preview")
        else:
            self.preview_popup.hide()
            self.preview_button.setText("Show Camera Preview")

    def _on_capture_clicked(self):
        """Handle capture button click."""
        self._set_controls_enabled(False)

        self.state = (
            self.STATE_AF if self.af_checkbox.isChecked() else self.STATE_CAPTURE
        )

        if self.state == self.STATE_AF:
            self.picam2.autofocus_cycle(
                signal_function=self.preview_popup.qpicamera2.signal_done
            )
        else:
            self._do_capture()

    def _do_capture(self):
        """Perform image capture."""
        cfg = self.picam2.create_still_configuration()
        filename = self.file_manager.get_next_filename("output")
        self.picam2.switch_mode_and_capture_file(
            cfg, filename, signal_function=self.preview_popup.qpicamera2.signal_done
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
        self.capture_button.setEnabled(enabled)
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
        if self.preview_popup:
            self.preview_popup.close()
        if self.speech_widget:
            self.speech_widget.closeEvent(event)
        event.accept()
