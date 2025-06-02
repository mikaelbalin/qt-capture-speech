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

        # Get preview dimensions
        preview_width, preview_height = CameraConfig.get_preview_size(self.picam2)

        # Create camera preview widget
        bg_colour = self.palette().color(QPalette.Background).getRgb()[:3]
        self.qpicamera2 = QGlPicamera2(
            self.picam2, width=preview_width, height=preview_height, bg_colour=bg_colour
        )

        layout = QVBoxLayout()
        layout.addWidget(self.qpicamera2)
        self.setLayout(layout)

        # Set window size
        self.resize(preview_width + 20, preview_height + 40)

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

        # Create camera controls panel
        camera_panel = self._create_camera_controls_panel()

        # Create speech recognition panel
        self.speech_widget = SpeechRecognitionWidget()
        speech_frame = QFrame()
        speech_frame.setFrameStyle(QFrame.StyledPanel)
        speech_frame.setMinimumWidth(100)

        speech_layout = QVBoxLayout()
        speech_layout.setContentsMargins(5, 5, 5, 5)
        speech_layout.addWidget(self.speech_widget)
        speech_frame.setLayout(speech_layout)

        # Main layout - direct horizontal layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(camera_panel, 1)  # Camera controls take 1/2 of space
        main_layout.addWidget(speech_frame, 1)  # Speech takes 1/2 of space
        self.setLayout(main_layout)

        # Set window size (much smaller now without preview)
        self.resize(800, 400)

    def _create_camera_controls_panel(self):
        """Create the camera controls panel widget."""
        camera_widget = QWidget()

        # Create camera controls
        self._create_camera_controls()

        # Camera controls layout
        layout_v_camera = QVBoxLayout()

        # Add preview toggle button
        layout_v_camera.addWidget(self.preview_button)

        # Add other controls
        layout_h_controls = QHBoxLayout()
        layout_h_controls.addWidget(self.continuous_checkbox)
        layout_h_controls.addWidget(self.af_checkbox)
        layout_h_controls.addWidget(self.capture_button)

        layout_v_camera.addLayout(layout_h_controls)

        camera_widget.setLayout(layout_v_camera)
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
