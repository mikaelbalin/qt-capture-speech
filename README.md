# Qt Camera & Speech Recognition Application

Qt-based application for camera capture and real-time speech recognition using Google Cloud Speech-to-Text.

## Requirements

### System Requirements

- Python 3.7 or higher
- Camera device (webcam)
- Microphone
- Internet connection (for Google Cloud Speech API)

### Dependencies

You can install the required packages by running:

```bash
pip install -r requirements.txt
```

### Note for Raspberry Pi Users

On Raspberry Pi, PyQt5 compilation often fails due to missing Qt development tools. To avoid this:

1. **Install system packages first**:

   ```bash
   sudo apt update
   sudo apt install portaudio19-dev
   ```

2. **Create virtual environment with system site packages**:

   ```bash
   python3 -m venv .venv --system-site-packages
   source .venv/bin/activate
   ```

3. **Install remaining requirements**:
   ```bash
   pip install google-cloud-speech numpy opencv-python pyaudio PyYAML
   ```

### Note for macOS Users

If you encounter issues installing `pyaudio`, install PortAudio first:

```bash
brew install portaudio
pip install pyaudio
```

## Configuration

### Google Cloud Setup

1. **Create a Google Cloud Project**:

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Speech-to-Text API**:

   - Navigate to APIs & Services > Library
   - Search for "Cloud Speech-to-Text API"
   - Click "Enable"

3. **Create Service Account**:

   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "Service Account"
   - Download the JSON key file

4. **Set Environment Variable**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
   ```

### Application Configuration

Edit `config/app_config.yaml` to customize settings:

```yaml
camera:
  device_id: 0 # Camera device ID
  width: 640 # Camera resolution width
  height: 480 # Camera resolution height
  fps: 30 # Frames per second

speech:
  language_code: "en-US" # Speech recognition language
  sample_rate: 16000 # Audio sample rate
  interim_results: true # Show interim results

files:
  output_directory: "output" # Output directory for files
  image_directory: "images" # Subdirectory for images
```

## Usage

### Running the Application

```bash
# From project root
python main.py

# Or if installed as package
qt-camera-speech
```

## Development

### Installing for Development

```bash
# Clone repository
git clone <repository-url>
cd qt-capture-speech

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-qt black flake8
```

### Logging

Application logs are saved to `app.log` by default. Adjust logging level in configuration:

```yaml
logging:
  level: "DEBUG" # DEBUG, INFO, WARNING, ERROR
  file: "app.log"
```
