#!/bin/bash

# Quick launcher for testing the Logic Keys OSC Controller app
APP_PATH="dist/Logic Keys OSC Controller.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found at: $APP_PATH"
    echo "Run ./build_app.sh first to build the app."
    exit 1
fi

echo "🚀 Launching Logic Keys OSC Controller..."
echo "💡 Make sure to grant Accessibility permissions when prompted!"
echo ""

open "$APP_PATH"

echo "✅ App launched! Check your menu bar or Activity Monitor to see if it's running."
echo ""
echo "📋 Quick test:"
echo "- Press 'R' to send mute signal (value 0)"
echo "- Press 'Space' to send unmute signal (value 1)"
echo "- Press Cmd+Q to quit the app"
