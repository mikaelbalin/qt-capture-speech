import pyaudio
import threading
import logging
from typing import Optional, Generator
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, StreamingRecognitionConfig
import queue

from ..core.interfaces import SpeechServiceInterface, ConfigManagerInterface
from ..core.exceptions import (
    SpeechInitializationError,
    SpeechRecognitionError,
    AudioDeviceError,
)


class SpeechService(SpeechServiceInterface):
    """Enhanced speech recognition service with proper streaming and resource management."""

    def __init__(self, config_manager: ConfigManagerInterface):
        super().__init__()
        self.config = config_manager
        self.logger = logging.getLogger(__name__)

        # Google Cloud Speech client
        self.client: Optional[speech.SpeechClient] = None

        # Audio configuration
        self.sample_rate = self.config.get("speech.sample_rate", 16000)
        self.chunk_size = self.config.get("speech.chunk_size", 1024)
        self.channels = self.config.get("speech.channels", 1)
        self.language_code = self.config.get("speech.language_code", "en-US")
        self.interim_results = self.config.get("speech.interim_results", True)

        # PyAudio setup
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # Threading
        self.audio_queue = queue.Queue()
        self.recognition_thread: Optional[threading.Thread] = None
        self.is_recording = False
        self.should_stop = threading.Event()

    def initialize(self) -> bool:
        """Initialize speech recognition service."""
        try:
            if self.client is not None:
                self.logger.warning("Speech service already initialized")
                return True

            # Initialize Google Cloud Speech client
            self.client = speech.SpeechClient()

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()

            # Test audio device
            self._test_audio_device()

            self.logger.info("Speech recognition service initialized")
            return True

        except Exception as e:
            error_msg = f"Speech service initialization failed: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.cleanup()
            return False

    def _test_audio_device(self) -> None:
        """Test if audio device is available and working."""
        try:
            # Try to open and immediately close a test stream
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            test_stream.close()

        except Exception as e:
            raise AudioDeviceError(f"Audio device test failed: {str(e)}")

    def start_recognition(self) -> bool:
        """Start speech recognition."""
        try:
            if not self.client:
                if not self.initialize():
                    return False

            if self.is_recording:
                self.logger.warning("Speech recognition already running")
                return True

            # Clear previous state
            self.should_stop.clear()
            while not self.audio_queue.empty():
                self.audio_queue.get()

            # Start audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback,
            )

            # Start recognition thread
            self.recognition_thread = threading.Thread(
                target=self._recognition_worker, daemon=True
            )
            self.recognition_thread.start()

            self.stream.start_stream()
            self.is_recording = True
            self.recording_status_changed.emit(True)

            self.logger.info("Speech recognition started")
            return True

        except Exception as e:
            error_msg = f"Failed to start speech recognition: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def stop_recognition(self) -> None:
        """Stop speech recognition."""
        try:
            self.should_stop.set()
            self.is_recording = False

            # Stop audio stream
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            # Wait for recognition thread to finish
            if self.recognition_thread and self.recognition_thread.is_alive():
                self.recognition_thread.join(timeout=2.0)

            self.recording_status_changed.emit(False)
            self.logger.info("Speech recognition stopped")

        except Exception as e:
            error_msg = f"Error stopping speech recognition: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for audio data."""
        if status:
            self.logger.warning(f"Audio callback status: {status}")

        if not self.should_stop.is_set():
            self.audio_queue.put(in_data)

        return (None, pyaudio.paContinue)

    def _audio_generator(self) -> Generator[bytes, None, None]:
        """Generate audio chunks for streaming recognition."""
        while not self.should_stop.is_set():
            try:
                # Get audio data with timeout
                chunk = self.audio_queue.get(timeout=0.1)
                yield chunk
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Audio generator error: {str(e)}")
                break

    def _recognition_worker(self) -> None:
        """Worker thread for speech recognition."""
        try:
            # Configure recognition
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=self.sample_rate,
                language_code=self.language_code,
            )

            streaming_config = StreamingRecognitionConfig(
                config=config,
                interim_results=self.interim_results,
            )

            # Create audio generator
            audio_generator = self._audio_generator()
            requests = (
                speech.StreamingRecognizeRequest(audio_content=chunk)
                for chunk in audio_generator
            )

            # Start streaming recognition
            responses = self.client.streaming_recognize(
                config=streaming_config, requests=requests
            )

            # Process responses
            self._process_responses(responses)

        except Exception as e:
            error_msg = f"Speech recognition error: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _process_responses(self, responses) -> None:
        """Process streaming recognition responses."""
        try:
            for response in responses:
                if self.should_stop.is_set():
                    break

                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    self.transcription_received.emit(transcript.strip())
                elif self.interim_results:
                    # Emit interim results with a special marker
                    self.transcription_received.emit(f"[INTERIM] {transcript}")

        except Exception as e:
            if not self.should_stop.is_set():
                error_msg = f"Error processing speech responses: {str(e)}"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)

    def cleanup(self) -> None:
        """Cleanup speech recognition resources."""
        try:
            self.stop_recognition()

            if self.audio:
                self.audio.terminate()
                self.audio = None

            self.client = None

            self.logger.info("Speech recognition resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during speech cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
