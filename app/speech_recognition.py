import queue
import re
import os
import threading

from google.cloud import speech
import pyaudio
from PyQt5.QtCore import QObject, pyqtSignal

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate: int = RATE, chunk: int = CHUNK) -> None:
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


class SpeechRecognition(QObject):
    """Speech recognition handler with Qt signals for GUI integration."""

    transcript_updated = pyqtSignal(str, bool)  # transcript, is_final
    error_occurred = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    initialization_complete = pyqtSignal()  # New signal for initialization completion

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.stream = None
        self.client = None
        self.recognition_thread = None
        self._is_initialized = False
        self._setup_client()

    def _setup_client(self):
        """Initialize Google Speech client."""
        try:
            # Set credentials path relative to project root
            credentials_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "service-account-key.json",
            )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.client = speech.SpeechClient()
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize speech client: {e}")

    def start_recording(self):
        """Start speech recognition in a separate thread."""
        if self.is_recording or not self.client:
            return

        self.is_recording = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        self.recording_started.emit()

    def stop_recording(self):
        """Stop speech recognition."""
        self.is_recording = False
        if self.stream:
            self.stream.closed = True
        self.recording_stopped.emit()

    def _recognition_loop(self):
        """Main recognition loop running in separate thread."""
        try:
            language_code = "en-US"
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code=language_code,
            )

            streaming_config = speech.StreamingRecognitionConfig(
                config=config, interim_results=True
            )

            with MicrophoneStream(RATE, CHUNK) as stream:
                self.stream = stream
                audio_generator = stream.generator()
                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )

                responses = self.client.streaming_recognize(streaming_config, requests)
                self._process_responses(responses)

        except Exception as e:
            self.error_occurred.emit(f"Recognition error: {e}")
        finally:
            self.is_recording = False
            self.recording_stopped.emit()

    def _process_responses(self, responses):
        """Process speech recognition responses."""
        for response in responses:
            if not self.is_recording:
                break

            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            is_final = result.is_final

            self.transcript_updated.emit(transcript, is_final)

            if is_final and re.search(r"\b(exit|quit)\b", transcript, re.I):
                self.stop_recording()
                break

    def _prepare_recognition(self):
        """Pre-initialize speech recognition components to avoid cold start delays."""
        if self._is_initialized or not self.client:
            return

        try:
            # Pre-initialize audio interface to warm up the system
            audio_interface = pyaudio.PyAudio()

            # Test microphone access and get default input device info
            default_device = audio_interface.get_default_input_device_info()

            # Brief initialization of audio stream to warm up the audio system
            test_stream = audio_interface.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )

            # Read a small amount of audio data to fully initialize
            test_stream.read(CHUNK, exception_on_overflow=False)

            # Clean up test objects
            test_stream.stop_stream()
            test_stream.close()
            audio_interface.terminate()

            # Test speech client connection with a minimal config
            test_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code="en-US",
            )

            self._is_initialized = True
            self.initialization_complete.emit()

        except Exception as e:
            print(f"Warning: Could not pre-warm speech recognition: {e}")
            # Don't emit error signal as this is just optimization
