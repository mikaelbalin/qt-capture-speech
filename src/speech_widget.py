from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QApplication,
)
from PyQt5.QtCore import Qt

from speech_recognition import SpeechRecognition


class SpeechRecognitionWidget(QWidget):
    """Widget for speech recognition functionality."""

    def __init__(self):
        super().__init__()
        self.speech_recognition = SpeechRecognition()
        self.current_transcript = ""
        self.final_transcript = ""
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the speech recognition UI."""
        layout = QVBoxLayout()

        # Transcript display
        self.transcript_display = QTextEdit()
        self.transcript_display.setReadOnly(True)
        self.transcript_display.setPlaceholderText("Transcript will appear here...")
        self.transcript_display.setMinimumHeight(200)
        layout.addWidget(self.transcript_display)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        self.copy_button = QPushButton("Copy Transcript")
        self.copy_button.clicked.connect(self._on_copy_clicked)
        button_layout.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _connect_signals(self):
        """Connect speech recognition signals to UI updates."""
        self.speech_recognition.transcript_updated.connect(self._on_transcript_updated)
        self.speech_recognition.error_occurred.connect(self._on_error)
        self.speech_recognition.recording_started.connect(self._on_recording_started)
        self.speech_recognition.recording_stopped.connect(self._on_recording_stopped)

    def _on_start_clicked(self):
        """Handle start recording button click."""
        self.speech_recognition.start_recording()

    def _on_stop_clicked(self):
        """Handle stop recording button click."""
        self.speech_recognition.stop_recording()

    def _on_copy_clicked(self):
        """Copy transcript to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.final_transcript)
        self.status_label.setText("Transcript copied to clipboard!")

    def _on_clear_clicked(self):
        """Clear transcript display."""
        self.transcript_display.clear()
        self.current_transcript = ""
        self.final_transcript = ""
        self.status_label.setText("Transcript cleared")

    def _on_transcript_updated(self, transcript, is_final):
        """Update transcript display."""
        if is_final:
            self.final_transcript += transcript + " "
            self.current_transcript = ""
            display_text = self.final_transcript
        else:
            self.current_transcript = transcript
            display_text = self.final_transcript + f"[{transcript}]"

        self.transcript_display.setPlainText(display_text)

        # Scroll to bottom
        cursor = self.transcript_display.textCursor()
        cursor.movePosition(cursor.End)
        self.transcript_display.setTextCursor(cursor)

    def _on_error(self, error_message):
        """Handle speech recognition errors."""
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: red; font-size: 12px;")

    def _on_recording_started(self):
        """Update UI when recording starts."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Recording... Speak now")
        self.status_label.setStyleSheet("color: green; font-size: 12px;")

    def _on_recording_stopped(self):
        """Update UI when recording stops."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Recording stopped")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")

    def closeEvent(self, event):
        """Handle widget close event."""
        if self.speech_recognition.is_recording:
            self.speech_recognition.stop_recording()
        event.accept()
