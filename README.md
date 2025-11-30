# Logic Keys OSC Controller

A macOS application that sends OSC messages to control Logic Pro X or XR18 mixer via keyboard shortcuts.

## Features
- Press **R** to mute (sends value 0)
- Press **Space** to unmute (sends value 1)
- Configurable IP address and OSC path
- Native macOS app bundle

## Configuration

Edit the configuration section in `main.py`:

```python
XR18_IP = "192.168.1.18"      # IP address of your XR18/Logic Pro X
XR18_PORT = 10024             # OSC port (default for XR18)
MUTE_PATH = "/bus/1/mix/on"   # OSC path to control
```

## Building the macOS App

1. Install dependencies:
   ```bash
   pipenv install --dev
   ```

2. Build the app:
   ```bash
   ./build_app.sh
   ```

3. Install the app:
   - Copy `dist/Logic Keys OSC Controller.app` to your Applications folder
   - Launch the app from Applications

## Permissions

When you first run the app, macOS will ask for:
- **Accessibility permissions** - Required to monitor keyboard input
- Go to System Preferences > Security & Privacy > Privacy > Accessibility
- Add and enable "Logic Keys OSC Controller"

## Troubleshooting

- If the app doesn't respond to key presses, check Accessibility permissions
- Verify your IP address and port configuration
- Check that your target device (XR18/Logic Pro X) is accepting OSC messages
- Use Console.app to view app logs if needed

## Development

- `main.py` - Main application code
- `setup.py` - py2app configuration
- `build_app.sh` - Build script
- `Pipfile` - Python dependencies
# logic-keys
