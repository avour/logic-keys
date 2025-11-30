#!/bin/bash

echo "Building Logic Keys OSC Controller macOS App..."

# Install dependencies if not already installed
echo "Installing dependencies..."
pipenv install --dev

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "Building app bundle..."
pipenv run python setup.py py2app

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "App bundle created at: dist/Logic Keys OSC Controller.app"
    echo ""
    echo "📁 App Contents:"
    ls -la "dist/Logic Keys OSC Controller.app/Contents/"
    echo ""
    echo "🚀 To install the app:"
    echo "1. Copy 'dist/Logic Keys OSC Controller.app' to your Applications folder"
    echo "2. You may need to allow the app in System Preferences > Security & Privacy"
    echo ""
    echo "⚠️  Important: The app will need Accessibility permissions to monitor keyboard input."
    echo "macOS will prompt you to grant these permissions when you first run the app."
    echo "Go to System Preferences > Security & Privacy > Privacy > Accessibility"
    echo "and make sure 'Logic Keys OSC Controller' is checked."
else
    echo "❌ Build failed. Check the error messages above."
fi
