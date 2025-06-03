import os
import threading
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
import logging

from ..core.interfaces import FileManagerInterface, ConfigManagerInterface
from ..core.exceptions import FileOperationException


class FileManager(FileManagerInterface):
    """Thread-safe file manager for handling file operations."""

    def __init__(self, config_manager: ConfigManagerInterface):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # Configuration
        self.output_dir = self.config.get("files.output_directory", "output")
        self.image_dir = self.config.get("files.image_directory", "images")
        self.audio_dir = self.config.get("files.audio_directory", "audio")
        self.filename_template = self.config.get(
            "files.filename_template", "{prefix}_{timestamp}.{extension}"
        )

        # Ensure base directories exist
        self._ensure_base_directories()

    def _ensure_base_directories(self) -> None:
        """Ensure base output directories exist."""
        directories = [
            self.output_dir,
            os.path.join(self.output_dir, self.image_dir),
            os.path.join(self.output_dir, self.audio_dir),
        ]

        for directory in directories:
            self.ensure_directory(directory)

    def generate_filename(self, prefix: str = "capture", extension: str = "jpg") -> str:
        """Generate unique filename with timestamp."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                :-3
            ]  # Include milliseconds

            filename = self.filename_template.format(
                prefix=prefix, timestamp=timestamp, extension=extension
            )

            return filename

        except Exception as e:
            raise FileOperationException(f"Failed to generate filename: {str(e)}")

    def ensure_directory(self, path: str) -> bool:
        """Ensure directory exists with thread safety."""
        try:
            with self._lock:
                Path(path).mkdir(parents=True, exist_ok=True)
                return True

        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {str(e)}")
            return False

    def save_file(self, data: Any, filepath: str) -> bool:
        """Save data to file with proper error handling."""
        try:
            with self._lock:
                # Ensure parent directory exists
                parent_dir = os.path.dirname(filepath)
                if parent_dir and not self.ensure_directory(parent_dir):
                    raise FileOperationException(
                        f"Cannot create parent directory: {parent_dir}"
                    )

                # Handle different data types
                if isinstance(data, (bytes, bytearray)):
                    mode = "wb"
                elif isinstance(data, str):
                    mode = "w"
                    data = data.encode("utf-8") if mode == "wb" else data
                else:
                    raise FileOperationException(f"Unsupported data type: {type(data)}")

                # Write file
                with open(filepath, mode) as file:
                    file.write(data)

                self.logger.info(f"File saved: {filepath}")
                return True

        except Exception as e:
            error_msg = f"Failed to save file {filepath}: {str(e)}"
            self.logger.error(error_msg)
            raise FileOperationException(error_msg)

    def get_image_path(self, filename: str) -> str:
        """Get full path for image file."""
        return os.path.join(self.output_dir, self.image_dir, filename)

    def get_audio_path(self, filename: str) -> str:
        """Get full path for audio file."""
        return os.path.join(self.output_dir, self.audio_dir, filename)

    def get_output_path(self, filename: str) -> str:
        """Get full path for general output file."""
        return os.path.join(self.output_dir, filename)

    def file_exists(self, filepath: str) -> bool:
        """Check if file exists."""
        return os.path.isfile(filepath)

    def get_file_size(self, filepath: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return os.path.getsize(filepath)
        except OSError:
            return None

    def delete_file(self, filepath: str) -> bool:
        """Delete file with error handling."""
        try:
            with self._lock:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    self.logger.info(f"File deleted: {filepath}")
                    return True
                else:
                    self.logger.warning(f"File not found for deletion: {filepath}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to delete file {filepath}: {str(e)}")
            return False
