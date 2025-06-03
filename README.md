# Qt Camera & Speech Recognition Application

Qt-based application for camera capture and real-time speech recognition using Google Cloud Speech-to-Text.

## Dependencies

You can install the required packages by running:

```bash
pip install -r requirements.txt
```

### Note for Raspberry Pi Users

On Raspberry Pi, PyQt5 compilation often fails due to missing Qt development tools. To avoid this:

1. Install system packages first:

   ```bash
   sudo apt update
   sudo apt install portaudio19-dev
   ```

2. Create virtual environment with system site packages:

   ```bash
   python -m venv .venv --system-site-packages
   source .venv/bin/activate
   ```

3. Install remaining requirements:
   ```bash
   pip install google-cloud-speech pyaudio
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

## Running the Application

```bash
# From project root
python main.py

# Or if installed as package
qt-camera-speech
```
