"""
File Management Utilities
"""

import os
import glob


class FileManager:
    """Handle file operations for the camera application."""

    def __init__(self, base_path=None):
        """Initialize file manager with base path."""
        self.base_path = base_path or os.path.dirname(os.path.abspath(__file__))

    def get_next_filename(self, base_name="output"):
        """Find the next available filename by checking existing files."""
        pattern = os.path.join(self.base_path, f"{base_name}_*.jpg")
        existing_files = glob.glob(pattern)

        # Extract numbers from existing filenames
        numbers = []
        for file in existing_files:
            filename = os.path.basename(file)
            try:
                num = int(filename.split("_")[1].split(".")[0])
                numbers.append(num)
            except (IndexError, ValueError):
                continue

        # Start with 1, or increment from highest existing number
        next_num = 1 if not numbers else max(numbers) + 1
        return os.path.join(self.base_path, f"{base_name}_{next_num}.jpg")

    def get_latest_filename(self, base_name="output"):
        """Get the most recently created file with the given base name."""
        pattern = os.path.join(self.base_path, f"{base_name}_*.jpg")
        files = sorted(glob.glob(pattern))
        return os.path.basename(files[-1]) if files else None
