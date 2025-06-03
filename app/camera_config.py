"""
Camera Configuration Settings
"""


class CameraConfig:
    """Camera configuration utilities."""

    PREVIEW_WIDTH = 800

    @classmethod
    def get_preview_size(cls, picam2):
        """Calculate preview size based on sensor aspect ratio."""
        preview_height = (
            picam2.sensor_resolution[1]
            * cls.PREVIEW_WIDTH
            // picam2.sensor_resolution[0]
        )
        preview_height -= preview_height % 2
        return cls.PREVIEW_WIDTH, preview_height

    @classmethod
    def get_preview_config(cls, picam2):
        """Create preview configuration for the camera."""
        preview_width, preview_height = cls.get_preview_size(picam2)
        preview_size = (preview_width, preview_height)

        # Full FoV raw mode (2x2 binned)
        raw_size = tuple([v // 2 for v in picam2.camera_properties["PixelArraySize"]])

        return picam2.create_preview_configuration(
            {"size": preview_size}, raw={"size": raw_size}
        )
