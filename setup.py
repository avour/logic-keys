# -*- coding: utf-8 -*-
"""
Setup script for creating macOS app bundle using py2app
"""
from setuptools import setup
import sys

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'includes': ['jaraco.text', 'jaraco.functools', 'more_itertools'],
    'packages': ['pynput', 'rumps', 'pkg_resources'],
    # 'iconfile': 'app_icon.icns',  # Optional: add custom icon when available
    'plist': {
        'CFBundleName': 'Logic Keys OSC Controller',
        'CFBundleDisplayName': 'Logic Keys',
        'CFBundleGetInfoString': "OSC Controller for Logic Pro X/XR18",
        'CFBundleIdentifier': 'com.logickeys.osccontroller',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Logic Keys OSC Controller',
        'NSRequiresAquaSystemAppearance': False,
        'LSBackgroundOnly': False,  # Set to True if you want it to run in background only
        'LSUIElement': True,  # This makes it a menu bar app without dock icon
        'NSAppleEventsUsageDescription': 'This app needs to monitor keyboard input for OSC control.',
        'NSAppleEventsUsageDescriptionKey': 'This app needs to monitor keyboard input for OSC control.',
    }
}

setup(
    app=APP,
    name='Logic Keys OSC Controller',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    # setup_requires=['py2app'],
    # install_requires=['pynput', 'rumps', 'jaraco.text', 'jaraco.functools', 'more-itertools'],
)
