from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSlot
import logging

from ..core.interfaces import SpeechServiceInterface, FileManagerInterface


class SpeechWidget(QWidget):
    """Speech recognition widget with proper separation from business logic."""

    def __init__(
        self,
        speech_service: SpeechServiceInterface,
        file_manager: FileManagerInterface,
        parent=None,
    ):
        super().__init__(parent)
        self.speech_service = speech_service
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout()

        # Controls
        controls_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.clear_button = QPushButton("Clear Text")
        self.save_button = QPushButton("Save Transcript")

        self.stop_button.setEnabled(False)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addWidget(self.save_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Options
        options_layout = QHBoxLayout()
        self.interim_checkbox = QCheckBox("Show interim results")
        self.interim_checkbox.setChecked(True)
        options_layout.addWidget(self.interim_checkbox)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Transcription display
        self.transcription_text = QTextEdit()
        self.transcription_text.setPlaceholderText(
            "Speech transcription will appear here..."
        )
        self.transcription_text.setMinimumHeight(300)
        layout.addWidget(self.transcription_text)

        # Status
        self.status_label = QLabel("Speech Recognition: Stopped")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def connect_signals(self):
        """Connect signals and slots."""
        # Button signals
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.clear_button.clicked.connect(self.clear_text)
        self.save_button.clicked.connect(self.save_transcript)

        # Speech service signals
        self.speech_service.transcription_received.connect(self.add_transcription)
        self.speech_service.error_occurred.connect(self.handle_error)
        self.speech_service.recording_status_changed.connect(self.update_status)

    def start_recording(self):
        """Start speech recognition."""
        try:
            if self.speech_service.start_recognition():
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.status_label.setText("Speech Recognition: Starting...")
            else:
                self.show_error("Failed to start speech recognition")

        except Exception as e:
            self.logger.error(f"Error starting speech recognition: {str(e)}")
            self.show_error(f"Speech recognition error: {str(e)}")

    def stop_recording(self):
        """Stop speech recognition."""
        try:
            self.speech_service.stop_recognition()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Speech Recognition: Stopped")

        except Exception as e:
            self.logger.error(f"Error stopping speech recognition: {str(e)}")
            self.show_error(f"Error stopping speech recognition: {str(e)}")

    def clear_text(self):
        """Clear transcription text."""
        self.transcription_text.clear()

    def save_transcript(self):
        """Save transcription to file."""
        try:
            text = self.transcription_text.toPlainText()
            if not text.strip():
                self.show_error("No text to save")
                return

            filename = self.file_manager.generate_filename("transcript", "txt")
            filepath = self.file_manager.get_output_path(filename)

            if self.file_manager.save_file(text, filepath):
                self.show_info(f"Transcript saved: {filename}")
            else:
                self.show_error("Failed to save transcript")

        except Exception as e:
            self.logger.error(f"Error saving transcript: {str(e)}")
            self.show_error(f"Save error: {str(e)}")

    @pyqtSlot(str)
    def add_transcription(self, text: str):
        """Add transcription text to display."""
        try:
            # Handle interim results
            if text.startswith("[INTERIM]"):
                if not self.interim_checkbox.isChecked():
                    return
                text = text[9:].strip()  # Remove [INTERIM] prefix
                text = f"[...] {text}"

            # Add text with newline
            cursor = self.transcription_text.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText(text + "\n")

            # Auto-scroll to bottom
            scrollbar = self.transcription_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            self.logger.error(f"Error adding transcription: {str(e)}")

    @pyqtSlot(str)
    def handle_error(self, error_message: str):
        """Handle speech service errors."""
        self.show_error(error_message)

        # Reset UI state on error
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Speech Recognition: Error")

    @pyqtSlot(bool)
    def update_status(self, is_active: bool):
        """Update recording status."""
        if is_active:
            self.status_label.setText("Speech Recognition: Recording...")
        else:
            self.status_label.setText("Speech Recognition: Stopped")

    def show_error(self, message: str):
        """Show error message to user."""
        QMessageBox.critical(self, "Speech Recognition Error", message)

    def show_info(self, message: str):
        """Show info message to user."""
        QMessageBox.information(self, "Speech Recognition Info", message)

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.speech_service.cleanup()
        except Exception as e:
            self.logger.error(f"Error during speech widget cleanup: {str(e)}")
