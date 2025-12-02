from pynput import keyboard
import socket
import struct
import rumps
import threading
import time

# CONFIG
XR18_PORT = 10024         # Default OSC control port
MUTE_PATHS = ["/bus/1/mix/on", "/bus/2/mix/on"]  # Mute targets
MUTE_VALUE = 0
UNMUTE_VALUE = 1
RECONNECT_INTERVAL = 5    # Seconds between reconnection attempts

# MIDI Configuration values for toggle
MIDI_CONFIG_PATH = "/-prefs/midiconfig"
MIDI_DIN_RX_MODE = 1      # b0: din cc/pc rx enabled (bit 0 = 1)
MIDI_USB_DIN_PASSTHRU_MODE = 64  # b6: din midi ↔ usb midi passthru (bit 6 = 1, which is 2^6 = 64)

# Connection status tracking
connection_status = "Disconnected"
XR18_IP = None  # Will be set based on local network
sock = None
connection_lock = threading.Lock()

# MIDI mode tracking
current_midi_mode = "DIN_RX"  # Can be "DIN_RX" or "USB_DIN_PASSTHRU"

def get_xr18_ip():
    """Get XR18 IP based on local network (assumes XR18 is at .20)."""
    global XR18_IP
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Use the same network base with .20 for XR18
        network_base = ".".join(local_ip.split(".")[:3])
        XR18_IP = f"{network_base}.15"
        print(f"[INFO] Local IP: {local_ip}, XR18 IP: {XR18_IP}")
        return XR18_IP
    except Exception as e:
        print(f"[ERROR] Could not determine local network: {e}")
        return None

def create_socket():
    """Create and configure the UDP socket for OSC communication."""
    global sock, connection_status, XR18_IP
    
    # If no IP is set, get it from local network
    if not XR18_IP:
        get_xr18_ip()
        if not XR18_IP:
            connection_status = "No Network"
            print(f"[ERROR] Cannot create socket - could not determine XR18 IP")
            return False
    
    try:
        with connection_lock:
            if sock:
                sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)  # 5 second timeout for operations
            connection_status = "Connected"
            print(f"[INFO] Socket created and configured for {XR18_IP}")
            return True
    except Exception as e:
        connection_status = "Disconnected"
        print(f"[ERROR] Failed to create socket: {e}")
        return False

def test_connection():
    """Test the connection by sending a test OSC message."""
    global connection_status
    
    if not XR18_IP:
        connection_status = "No Network"
        return False
    
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
            for path in MUTE_PATHS:
                send_osc(path, MUTE_VALUE)  # Mute
    except AttributeError:
        if key == keyboard.Key.space:
            for path in MUTE_PATHS:
                send_osc(path, UNMUTE_VALUE)  # Unmute
    except Exception as e:
        print("[ERROR]", e)

def main():
    # Get XR18 IP based on local network
    if not XR18_IP:
        get_xr18_ip()
    
    if not XR18_IP:
        print(f"[ERROR] Could not determine network. Please check connection.")
        return
    
    print(f"[INFO] Logic Keys OSC Controller Started")
    print(f"[INFO] Target: {XR18_IP}:{XR18_PORT}")
    print(f"[INFO] OSC Paths: {MUTE_PATHS}")
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
        self.target_item = rumps.MenuItem("Target: Discovering...", callback=None)
        self.reconnect_item = rumps.MenuItem("Reconnect", callback=self.manual_reconnect)
        self.rescan_item = rumps.MenuItem("Refresh Network", callback=self.rescan_network)
        self.midi_mode_item = rumps.MenuItem("MIDI Mode: DIN RX", callback=None)
        self.toggle_keyboard_item = rumps.MenuItem("Toggle Keyboard", callback=self.toggle_keyboard_menu)
        
        self.menu = [
            self.status_item,
            None,  # Separator
            self.target_item,
            None,  # Separator
            self.midi_mode_item,
            self.toggle_keyboard_item,
            None,  # Separator
            self.reconnect_item,
            self.rescan_item,
            None,  # Separator
            rumps.MenuItem("Controls:", callback=None),
            rumps.MenuItem("  R = Mute Bus 1 & 2", callback=None),
            rumps.MenuItem("  Space = Unmute Bus 1 & 2", callback=None),
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
        elif connection_status == "No Network":
            self.status_item.title = "Status: ⚠️ No Network"
        else:
            self.status_item.title = "Status: ❌ Disconnected"
        
        # Update target display
        if XR18_IP:
            self.target_item.title = f"Target: {XR18_IP}:{XR18_PORT}"
        else:
            self.target_item.title = "Target: Not found"
        
        # Update MIDI mode display
        if current_midi_mode == "DIN_RX":
            self.midi_mode_item.title = "MIDI Mode: DIN RX"
        else:
            self.midi_mode_item.title = "MIDI Mode: USB-DIN Passthrough"
    
    def start_reconnect_monitor(self):
        """Start the automatic reconnection monitor in a background thread."""
        def reconnect_worker():
            global connection_status
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
    
    def rescan_network(self, _):
        """Refresh the XR18 IP based on current network."""
        global connection_status, XR18_IP
        print(f"[INFO] Network refresh requested")
        XR18_IP = None  # Reset IP to re-detect
        connection_status = "Connecting..."
        self.update_status_display()
        
        def rescan_task():
            if get_xr18_ip():
                create_socket()
            self.update_status_display()
        
        # Run in background to avoid blocking UI
        threading.Thread(target=rescan_task, daemon=True).start()
    
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
        if XR18_IP:
            print(f"[INFO] Target: {XR18_IP}:{XR18_PORT}")
        else:
            print(f"[INFO] Target: Auto-discovery enabled")
        print(f"[INFO] OSC Paths: {MUTE_PATHS}")
        print(f"[INFO] Controls: R = Mute Bus 1 & 2, Space = Unmute Bus 1 & 2")
    
    def quit_application(self, _):
        """Quit the application"""
        print("\n[INFO] Exiting...")
        if self.listener:
            self.listener.stop()
        rumps.quit_application()

if __name__ == "__main__":
    app = LogicKeysApp()
    app.run()
