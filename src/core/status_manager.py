"""
MIA_JETSON - Status Manager
Handles the temporary runtime state of the system as defined in PROJECT_ARCHITECTURE.md.
"""

class StatusManager:
    def __init__(self):
        # Initial status values
        self.is_online = False
        self.current_state = "idle"  # idle, listening, processing, speaking
        self.mic_active = False
        self.camera_active = False
        self.internet_available = False
        self.language = "en"  # Default language
        
        # Session data
        self.start_time = None
        self.last_command = None
        
    def update_connectivity(self, online_status):
        self.internet_available = online_status
        self.is_online = online_status
        
    def set_state(self, new_state):
        valid_states = ["idle", "listening", "processing", "speaking"]
        if new_state in valid_states:
            self.current_state = new_state
            print(f"[Status] System state changed to: {new_state}")
        else:
            print(f"[Status Warning] Invalid state attempt: {new_state}")

    def get_status_summary(self):
        """Returns a summary of the current system status."""
        return {
            "online": self.is_online,
            "state": self.current_state,
            "mic": self.mic_active,
            "camera": self.camera_active
        }
