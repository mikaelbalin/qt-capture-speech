#!/usr/bin/python3

from libcamera import controls
from PyQt5 import QtCore
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import os
import glob

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2

STATE_AF = 0
STATE_CAPTURE = 1


picam2 = Picamera2()
# Adjust the preview size to match the sensor aspect ratio.
preview_width = 800
preview_height = picam2.sensor_resolution[1] * 800 // picam2.sensor_resolution[0]
preview_height -= preview_height % 2
preview_size = (preview_width, preview_height)
# We also want a full FoV raw mode, this gives us the 2x2 binned mode.
raw_size = tuple([v // 2 for v in picam2.camera_properties["PixelArraySize"]])
preview_config = picam2.create_preview_configuration(
    {"size": preview_size}, raw={"size": raw_size}
)
picam2.configure(preview_config)
if "AfMode" not in picam2.camera_controls:
    print("Attached camera does not support autofocus")
    quit()
picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
app = QApplication([])


def get_next_filename(base_name="output"):
    """Find the next available filename by checking existing files."""
    # Get the directory where the script is running
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Find all existing files that match the pattern
    pattern = os.path.join(base_path, f"{base_name}_*.jpg")
    existing_files = glob.glob(pattern)

    # Extract numbers from existing filenames
    numbers = []
    for file in existing_files:
        # Extract number between underscore and .jpg
        filename = os.path.basename(file)
        try:
            num = int(filename.split("_")[1].split(".")[0])
            numbers.append(num)
        except (IndexError, ValueError):
            continue

    # Start with 1, or increment from highest existing number
    next_num = 1 if not numbers else max(numbers) + 1
    return os.path.join(base_path, f"{base_name}_{next_num}.jpg")


def on_button_clicked():
    global state
    button.setEnabled(False)
    continuous_checkbox.setEnabled(False)
    af_checkbox.setEnabled(False)
    state = STATE_AF if af_checkbox.isChecked() else STATE_CAPTURE
    if state == STATE_AF:
        picam2.autofocus_cycle(signal_function=qpicamera2.signal_done)
    else:
        do_capture()


def do_capture():
    cfg = picam2.create_still_configuration()
    filename = get_next_filename("output")
    picam2.switch_mode_and_capture_file(
        cfg, filename, signal_function=qpicamera2.signal_done
    )


def callback(job):
    global state
    if state == STATE_AF:
        state = STATE_CAPTURE
        success = "succeeded" if picam2.wait(job) else "failed"
        print(f"AF cycle {success} in {job.calls} frames")
        do_capture()
    else:
        picam2.wait(job)
        # Get the last captured filename to display in a message
        latest_files = sorted(
            glob.glob(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_*.jpg")
            )
        )
        if latest_files:
            latest_file = os.path.basename(latest_files[-1])
            print(f"Captured: {latest_file}")

        picam2.set_controls({"AfMode": controls.AfModeEnum.Auto})
        button.setEnabled(True)
        continuous_checkbox.setEnabled(True)
        af_checkbox.setEnabled(True)


def on_continuous_toggled(checked):
    mode = controls.AfModeEnum.Continuous if checked else controls.AfModeEnum.Auto
    picam2.set_controls({"AfMode": mode})


window = QWidget()
bg_colour = window.palette().color(QPalette.Background).getRgb()[:3]
qpicamera2 = QGlPicamera2(
    picam2, width=preview_width, height=preview_height, bg_colour=bg_colour
)
qpicamera2.done_signal.connect(callback, type=QtCore.Qt.QueuedConnection)

button = QPushButton("Click to capture JPEG")
button.clicked.connect(on_button_clicked)
af_checkbox = QCheckBox("AF before capture", checked=False)
continuous_checkbox = QCheckBox("Continuous AF", checked=False)
continuous_checkbox.toggled.connect(on_continuous_toggled)
window.setWindowTitle("Qt Picamera2 App")

# Replace the horizontal layout with a vertical layout
layout_v_main = QVBoxLayout()
layout_h_controls = QHBoxLayout()

# Add the preview to the main vertical layout
layout_v_main.addWidget(qpicamera2)

# Add controls to the horizontal layout
layout_h_controls.addWidget(continuous_checkbox)
layout_h_controls.addWidget(af_checkbox)
layout_h_controls.addWidget(button)

# Add the horizontal controls layout to the bottom of the main vertical layout
layout_v_main.addLayout(layout_h_controls)

# Set appropriate window size for vertical layout
window.resize(preview_width, preview_height + 80)
window.setLayout(layout_v_main)

picam2.start()
window.show()
app.exec()
picam2.stop()
