"""
File Management Utilities
"""

import os
import glob


class FileManager:
    """Handle file operations for the camera application."""

    def __init__(self, base_path=None):
        """Initialize file manager with base path."""
        if base_path:
            self.base_path = base_path
        else:
            # Get the directory of the current file (file_utils.py)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to get the project root (e.g., /home/project)
            project_root = os.path.dirname(current_file_dir)
            # Define the images directory
            self.base_path = os.path.join(project_root, "images")

        # Ensure the images directory exists
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

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
