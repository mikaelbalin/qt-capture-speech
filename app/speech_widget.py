from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QApplication,
    QSizePolicy,
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
        self._is_first_recording = True
        self._init_ui()
        self._connect_signals()
        # Pre-warm the speech recognition system
        self._warm_up_speech_recognition()

    def _init_ui(self):
        """Initialize the speech recognition UI."""
        layout = QVBoxLayout()

        # Transcript display at the top
        self.transcript_display = QTextEdit()
        self.transcript_display.setReadOnly(True)
        self.transcript_display.setPlaceholderText("Transcript will appear here...")
        self.transcript_display.setMinimumHeight(100)
        self.transcript_display.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        layout.addWidget(self.transcript_display)

        # Control buttons layout
        button_layout = QHBoxLayout()

        # Record toggle button on the left (takes more space)
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self._on_record_toggle_clicked)
        self.record_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_layout.addWidget(self.record_button, 2)  # Give it 2 parts of space

        # Right side buttons in vertical layout
        right_buttons = QVBoxLayout()

        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self._on_copy_clicked)
        right_buttons.addWidget(self.copy_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        right_buttons.addWidget(self.clear_button)

        button_layout.addLayout(right_buttons, 1)  # Give it 1 part of space

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _connect_signals(self):
        """Connect speech recognition signals to UI updates."""
        self.speech_recognition.transcript_updated.connect(self._on_transcript_updated)
        self.speech_recognition.error_occurred.connect(self._on_error)
        self.speech_recognition.recording_started.connect(self._on_recording_started)
        self.speech_recognition.recording_stopped.connect(self._on_recording_stopped)
        self.speech_recognition.initialization_complete.connect(
            self._on_initialization_complete
        )

    def _warm_up_speech_recognition(self):
        """Pre-initialize speech recognition to avoid cold start delays."""
        if self._is_first_recording:
            self.status_label.setText("Initializing speech recognition...")
            self.status_label.setStyleSheet("color: orange; font-size: 12px;")

            # Run preparation in a separate thread to avoid blocking UI
            import threading

            warm_up_thread = threading.Thread(
                target=self.speech_recognition._prepare_recognition
            )
            warm_up_thread.daemon = True
            warm_up_thread.start()

    def _on_initialization_complete(self):
        """Handle speech recognition initialization completion."""
        self._is_first_recording = False
        self.status_label.setText("Ready - Speech recognition initialized")
        self.status_label.setStyleSheet("color: green; font-size: 12px;")

    def _on_record_toggle_clicked(self):
        """Handle record toggle button click."""
        if self.speech_recognition.is_recording:
            self.speech_recognition.stop_recording()
            # Copy transcript to clipboard after stopping recording
            if self.final_transcript.strip():
                clipboard = QApplication.clipboard()
                clipboard.setText(self.final_transcript.strip())
                self.status_label.setText(
                    "Recording stopped - Transcript copied to clipboard!"
                )
        else:
            # Show appropriate status based on initialization state
            if self._is_first_recording:
                self.status_label.setText(
                    "Starting first recording (may take a moment)..."
                )
                self.status_label.setStyleSheet("color: orange; font-size: 12px;")
            else:
                self.status_label.setText("Starting recording...")
                self.status_label.setStyleSheet("color: blue; font-size: 12px;")

            # Clear transcript before starting new recording
            self.transcript_display.clear()
            self.current_transcript = ""
            self.final_transcript = ""
            self.speech_recognition.start_recording()

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
            self.final_transcript += transcript + "\n"
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
        self.record_button.setText("Stop Recording")
        self.status_label.setText("Recording... Speak now")
        self.status_label.setStyleSheet("color: green; font-size: 12px;")

    def _on_recording_stopped(self):
        """Update UI when recording stops."""
        self.record_button.setText("Start Recording")
        self.status_label.setText("Recording stopped")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")

    def closeEvent(self, event):
        """Handle widget close event."""
        if self.speech_recognition.is_recording:
            self.speech_recognition.stop_recording()
        event.accept()
