from pynput import keyboard
import socket
import struct
import rumps
import threading
import time

# CONFIG
XR18_IP = "192.168.1.20" 
XR18_PORT = 10024         # Default OSC control port
MUTE_PATH = "/bus/1/mix/on"  # Change to your desired mute target
MUTE_VALUE = 0
UNMUTE_VALUE = 1
RECONNECT_INTERVAL = 5    # Seconds between reconnection attempts

# MIDI Configuration values for toggle
MIDI_CONFIG_PATH = "/-prefs/midiconfig"
MIDI_DIN_RX_MODE = 1      # b0: din cc/pc rx enabled (bit 0 = 1)
MIDI_USB_DIN_PASSTHRU_MODE = 64  # b6: din midi ↔ usb midi passthru (bit 6 = 1, which is 2^6 = 64)

# Connection status tracking
connection_status = "Disconnected"
sock = None
connection_lock = threading.Lock()

# MIDI mode tracking
current_midi_mode = "DIN_RX"  # Can be "DIN_RX" or "USB_DIN_PASSTHRU"

def create_socket():
    """Create and configure the UDP socket for OSC communication."""
    global sock, connection_status
    try:
        with connection_lock:
            if sock:
                sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)  # 5 second timeout for operations
            connection_status = "Connected"
            print(f"[INFO] Socket created and configured")
            return True
    except Exception as e:
        connection_status = "Disconnected"
        print(f"[ERROR] Failed to create socket: {e}")
        return False

def test_connection():
    """Test the connection by sending a test OSC message."""
    global connection_status
    try:
        with connection_lock:
            if not sock:
                return False
            # Send a test message that shouldn't affect anything
            test_msg = osc_format("/info", 0)
            sock.sendto(test_msg, (XR18_IP, XR18_PORT))
            connection_status = "Connected"
            return True
    except Exception as e:
        connection_status = "Disconnected"
        print(f"[ERROR] Connection test failed: {e}")
        return False

def ensure_connection():
    """Ensure we have a working connection, create if needed."""
    if not sock or connection_status == "Disconnected":
        return create_socket()
    return test_connection()

def osc_format(path, value):
    """Format OSC message (string + int)."""
    def osc_pad(s):
        b = s.encode('utf-8') + b'\x00'
        return b + (b'\x00' * ((4 - (len(b) % 4)) % 4))

    def osc_int(i):
        return struct.pack(">i", i)

    msg = osc_pad(path) + osc_pad(",i") + osc_int(value)
    return msg

def send_osc(path, value):
    """Send OSC message with connection handling."""
    global connection_status
    
    # Ensure we have a connection
    if not ensure_connection():
        print(f"[ERROR] No connection available for OSC message")
        return False
    
    try:
        with connection_lock:
            msg = osc_format(path, value)
            sock.sendto(msg, (XR18_IP, XR18_PORT))
            connection_status = "Connected"
            print(f"[OSC] Sent {path} = {value}")
            return True
    except Exception as e:
        connection_status = "Disconnected"
        print(f"[ERROR] Failed to send OSC: {e}")
        return False

def toggle_keyboard_mode():
    """Toggle between DIN RX and USB-DIN passthrough modes."""
    global current_midi_mode
    
    if current_midi_mode == "DIN_RX":
        # Switch to USB-DIN passthrough mode
        if send_osc(MIDI_CONFIG_PATH, MIDI_USB_DIN_PASSTHRU_MODE):
            current_midi_mode = "USB_DIN_PASSTHRU"
            print(f"[MIDI] Switched to USB-DIN Passthrough mode")
            return True
    else:
        # Switch to DIN RX mode
        if send_osc(MIDI_CONFIG_PATH, MIDI_DIN_RX_MODE):
            current_midi_mode = "DIN_RX"
            print(f"[MIDI] Switched to DIN RX mode")
            return True
    
    return False

def on_press(key):
    try:
        if key.char and key.char.lower() == 'r':
            send_osc(MUTE_PATH, MUTE_VALUE)  # Mute
    except AttributeError:
        if key == keyboard.Key.space:
            send_osc(MUTE_PATH, UNMUTE_VALUE)  # Unmute
    except Exception as e:
        print("[ERROR]", e)

def main():
    print(f"[INFO] Logic Keys OSC Controller Started")
    print(f"[INFO] Target: {XR18_IP}:{XR18_PORT}")
    print(f"[INFO] OSC Path: {MUTE_PATH}")
    print(f"[INFO] Controls: R = Mute ({MUTE_VALUE}), Space = Unmute ({UNMUTE_VALUE})")
    print(f"[INFO] Press Ctrl+C to exit")
    
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n[INFO] Exiting...")
    except Exception as e:
        print(f"[ERROR] Application error: {e}")

class LogicKeysApp(rumps.App):
    def __init__(self):
        super(LogicKeysApp, self).__init__("🎹 Logic Keys", quit_button=None)
        
        # Menu items that we need to update dynamically
        self.status_item = rumps.MenuItem("Status: Connecting...", callback=None)
        self.reconnect_item = rumps.MenuItem("Reconnect", callback=self.manual_reconnect)
        self.midi_mode_item = rumps.MenuItem("MIDI Mode: DIN RX", callback=None)
        self.toggle_keyboard_item = rumps.MenuItem("Toggle Keyboard", callback=self.toggle_keyboard_menu)
        
        self.menu = [
            self.status_item,
            None,  # Separator
            rumps.MenuItem("Target: " + XR18_IP + ":" + str(XR18_PORT), callback=None),
            None,  # Separator
            self.midi_mode_item,
            self.toggle_keyboard_item,
            None,  # Separator
            self.reconnect_item,
            None,  # Separator
            rumps.MenuItem("Controls:", callback=None),
            rumps.MenuItem("  R = Mute (" + str(MUTE_VALUE) + ")", callback=None),
            rumps.MenuItem("  Space = Unmute (" + str(UNMUTE_VALUE) + ")", callback=None),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_application)
        ]
        
        # Start keyboard listener in backgrround thread
        self.listener_thread = None
        self.listener = None
        self.reconnect_thread = None
        self.should_reconnect = True
        
        # Initialize connection and start background processes
        self.start_connection()
        self.start_listener()
        self.start_reconnect_monitor()
    
    def start_connection(self):
        """Initialize the socket connection."""
        global connection_status
        connection_status = "Connecting..."
        self.update_status_display()
        
        if create_socket():
            print(f"[INFO] Initial connection established")
        else:
            print(f"[WARNING] Initial connection failed, will retry automatically")
    
    def update_status_display(self):
        """Update the status menu item based on current connection status."""
        if connection_status == "Connected":
            self.status_item.title = "Status: ✅ Connected"
        elif connection_status == "Connecting...":
            self.status_item.title = "Status: 🔄 Connecting..."
        else:
            self.status_item.title = "Status: ❌ Disconnected"
        
        # Update MIDI mode display
        if current_midi_mode == "DIN_RX":
            self.midi_mode_item.title = "MIDI Mode: DIN RX"
        else:
            self.midi_mode_item.title = "MIDI Mode: USB-DIN Passthrough"
    
    def start_reconnect_monitor(self):
        """Start the automatic reconnection monitor in a background thread."""
        def reconnect_worker():
            while self.should_reconnect:
                try:
                    # Update status display
                    self.update_status_display()
                    
                    # Check connection and reconnect if needed
                    if connection_status == "Disconnected":
                        print(f"[INFO] Connection lost, attempting to reconnect...")
                        connection_status = "Connecting..."
                        self.update_status_display()
                        
                        if create_socket():
                            print(f"[INFO] Reconnection successful")
                        else:
                            print(f"[WARNING] Reconnection failed, will retry in {RECONNECT_INTERVAL} seconds")
                    
                    time.sleep(RECONNECT_INTERVAL)
                except Exception as e:
                    print(f"[ERROR] Reconnect monitor error: {e}")
                    time.sleep(RECONNECT_INTERVAL)
        
        self.reconnect_thread = threading.Thread(target=reconnect_worker, daemon=True)
        self.reconnect_thread.start()
        print(f"[INFO] Auto-reconnection monitor started")
    
    def manual_reconnect(self, _):
        """Manual reconnection triggered by user."""
        global connection_status
        print(f"[INFO] Manual reconnection requested")
        connection_status = "Connecting..."
        self.update_status_display()
        
        def reconnect_task():
            if create_socket():
                print(f"[INFO] Manual reconnection successful")
            else:
                print(f"[ERROR] Manual reconnection failed")
            self.update_status_display()
        
        # Run reconnection in background to avoid blocking UI
        threading.Thread(target=reconnect_task, daemon=True).start()
    
    def toggle_keyboard_menu(self, _):
        """Toggle keyboard mode triggered by menu click."""
        def toggle_task():
            if toggle_keyboard_mode():
                self.update_status_display()
        
        # Run toggle in background to avoid blocking UI
        threading.Thread(target=toggle_task, daemon=True).start()
    
    def start_listener(self):
        """Start the keyboard listener in a background thread"""
        def listener_worker():
            try:
                with keyboard.Listener(on_press=on_press) as listener:
                    self.listener = listener
                    listener.join()
            except Exception as e:
                print(f"[ERROR] Listener error: {e}")
        
        self.listener_thread = threading.Thread(target=listener_worker, daemon=True)
        self.listener_thread.start()
        print(f"[INFO] Logic Keys OSC Controller Started")
        print(f"[INFO] Target: {XR18_IP}:{XR18_PORT}")
        print(f"[INFO] OSC Path: {MUTE_PATH}")
        print(f"[INFO] Controls: R = Mute ({MUTE_VALUE}), Space = Unmute ({UNMUTE_VALUE})")
    
    def quit_application(self, _):
        """Quit the application"""
        print("\n[INFO] Exiting...")
        if self.listener:
            self.listener.stop()
        rumps.quit_application()

if __name__ == "__main__":
    app = LogicKeysApp()
    app.run()
