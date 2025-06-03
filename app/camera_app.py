"""
Camera Application GUI and Logic
"""

import os
from PyQt5 import QtCore
from PyQt5.QtGui import QPalette, QPixmap, QIcon
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
    QListWidget,
    QListWidgetItem,
    QApplication,
)
from PyQt5.QtCore import Qt, QSize
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


class SnapshotListWidget(QWidget):
    """Widget for displaying recent snapshots with copy functionality."""

    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self._init_ui()
        self.refresh_snapshots()

    def _init_ui(self):
        """Initialize the snapshot list UI."""
        layout = QVBoxLayout()

        # List widget for snapshots
        self.snapshot_list = QListWidget()
        self.snapshot_list.setMaximumHeight(130)  # Increased height for thumbnails

        # Set icon size for thumbnails
        self.snapshot_list.setIconSize(QSize(60, 45))  # 4:3 aspect ratio

        # Set item spacing
        self.snapshot_list.setSpacing(2)

        layout.addWidget(self.snapshot_list)

        self.setLayout(layout)

    def _on_selection_changed(self):
        """Handle selection change in the list."""
        # This method is kept for potential future use
        pass

    def get_selected_image_path(self):
        """Get the full path of the selected image."""
        selected_items = self.snapshot_list.selectedItems()
        if selected_items:
            filename = selected_items[0].text()
            return os.path.join(self.file_manager.base_path, filename)
        return None

    def refresh_snapshots(self):
        """Refresh the list of recent snapshots."""
        self.snapshot_list.clear()
        recent_files = self.file_manager.get_recent_files("output", 5)

        for filename in recent_files:
            # Create list item
            item = QListWidgetItem(filename)

            # Load image as thumbnail
            full_path = os.path.join(self.file_manager.base_path, filename)
            try:
                pixmap = QPixmap(full_path)
                if not pixmap.isNull():
                    # Scale pixmap to thumbnail size while maintaining aspect ratio
                    thumbnail = pixmap.scaled(
                        60, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    item.setIcon(QIcon(thumbnail))
                else:
                    print(f"Failed to load thumbnail for: {filename}")
            except Exception as e:
                print(f"Error loading thumbnail for {filename}: {e}")

            self.snapshot_list.addItem(item)


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
        self.snapshot_widget = None

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
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})

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

        # Create snapshot list widget first
        self.snapshot_widget = SnapshotListWidget(self.file_manager)

        # Create camera controls (now that snapshot_widget exists)
        self._create_camera_controls()

        # Connect snapshot selection to copy button state
        self.snapshot_widget.snapshot_list.itemSelectionChanged.connect(
            self._on_snapshot_selection_changed
        )

        # Main horizontal layout for camera section
        main_camera_layout = QHBoxLayout()

        # Left side - Recent snapshots
        self.snapshot_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        main_camera_layout.addWidget(self.snapshot_widget, 0)  # Fixed size

        # Add vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #ccc; }")
        main_camera_layout.addWidget(separator)

        # Right side - Camera controls
        camera_controls_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add spacing between buttons

        # First row - Capture button (full width)
        self.capture_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.capture_button, 1)

        # Second row - Copy and Preview buttons
        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(10)

        self.copy_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        second_row_layout.addWidget(self.copy_button, 1)
        second_row_layout.addWidget(self.preview_button, 1)

        layout.addLayout(second_row_layout, 1)

        camera_controls_widget.setLayout(layout)
        main_camera_layout.addWidget(camera_controls_widget, 1)  # Takes remaining space

        camera_widget.setLayout(main_camera_layout)
        return camera_widget

    def _create_camera_controls(self):
        """Create camera UI controls."""
        self.preview_button = QPushButton("Preview")
        self.preview_button.setCheckable(True)
        self.preview_button.clicked.connect(self._on_preview_toggle)

        self.capture_button = QPushButton("Capture")
        self.capture_button.clicked.connect(self._on_capture_clicked)

        # Create copy button
        self.copy_button = QPushButton("Copy Image")
        self.copy_button.clicked.connect(self._on_copy_clicked)
        self.copy_button.setEnabled(False)

        self.af_checkbox = QCheckBox("AF before capture", checked=True)
        self.continuous_checkbox = QCheckBox("Continuous AF", checked=True)
        self.continuous_checkbox.toggled.connect(self._on_continuous_toggled)

    def _on_preview_toggle(self, checked):
        """Handle preview toggle button."""
        if checked:
            self.preview_popup.show()
            self.preview_button.setText("Hide Preview")
        else:
            self.preview_popup.hide()
            self.preview_button.setText("Show Preview")

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
                # Automatically copy the captured image to clipboard
                self._copy_image_to_clipboard(latest_file)

            # Refresh snapshot list
            if self.snapshot_widget:
                self.snapshot_widget.refresh_snapshots()

            # Reset camera and UI
            self.picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
            self._set_controls_enabled(True)

    def _copy_image_to_clipboard(self, filename):
        """Copy the specified image file to clipboard."""
        if not filename:
            return

        image_path = os.path.join(self.file_manager.base_path, filename)
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                clipboard = QApplication.clipboard()
                clipboard.setPixmap(pixmap)
                print(f"Auto-copied image to clipboard: {filename}")
            else:
                print(f"Failed to load captured image: {image_path}")
        except Exception as e:
            print(f"Error auto-copying image: {e}")

    def _on_continuous_toggled(self, checked):
        """Handle continuous autofocus toggle."""
        mode = controls.AfModeEnum.Continuous if checked else controls.AfModeEnum.Auto
        self.picam2.set_controls({"AfMode": mode})

    def _set_controls_enabled(self, enabled):
        """Enable or disable UI controls."""
        self.capture_button.setEnabled(enabled)

    def _on_copy_clicked(self):
        """Handle copy button click."""
        if self.snapshot_widget:
            image_path = self.snapshot_widget.get_selected_image_path()
            if image_path:
                filename = os.path.basename(image_path)
                self._copy_image_to_clipboard(filename)

    def _on_snapshot_selection_changed(self):
        """Handle snapshot selection change to enable/disable copy button."""
        has_selection = bool(self.snapshot_widget.snapshot_list.selectedItems())
        self.copy_button.setEnabled(has_selection)

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
