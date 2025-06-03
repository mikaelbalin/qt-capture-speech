## Requirements

You can install the required packages by running:

```
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

3. **Install only the remaining requirements**:
   ```bash
   pip install google-cloud-speech numpy
   ```

### Note for macOS Users

If you encounter issues installing `pyaudio`, you may need to install the PortAudio library first:

```
brew install portaudio
```

Then, reinstall pyaudio:

```
pip uninstall pyaudio
pip install pyaudio
```

## Configuration

1.  **Google Cloud Setup**: Ensure you have a Google Cloud Platform project with the Speech-to-Text API enabled.
2.  **Service Account Key**: Create a service account, grant it appropriate permissions (e.g., "Cloud Speech Service Agent"), and download its JSON key file.
