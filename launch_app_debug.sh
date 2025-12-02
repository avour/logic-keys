#!/bin/bash

# Debug launcher for Logic Keys OSC Controller app
APP_PATH="dist/Logic Keys OSrC Controller.app"
# APP_PATH="/Applications/Logic Keys OSC Controller.app"
EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/Logic Keys OSC Controller"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found at: $APP_PATH"
    echo "Run ./build_app.sh first to build the app."
    exit 1
fi

echo "🐛 Launching Logic Keys OSC Controller in DEBUG mode..."
echo "💡 This will show all console output and error messages"
echo "📍 App path: $APP_PATH"
echo ""

# Kill any existing instance first
echo "🔄 Killing any existing instances..."
pkill -f "Logic Keys OSC Controller" 2>/dev/null || true

echo "🚀 Starting app with debug output..."
echo "----------------------------------------"

# Launch the executable directly to see console output
cd "$(dirname "$EXECUTABLE_PATH")"
exec "./Logic Keys OSC Controller"

echo "----------------------------------------"
echo "🛑 App has exited. Check output above for any errors."
