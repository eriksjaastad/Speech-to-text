#!/usr/bin/env python3
"""
Erik's Personal Speech-to-Text Tool - Menubar Application
Wraps the main STT logic in a macOS menu bar app using rumps.
"""

import rumps
import threading
import time
from src.main import ErikSTT
# Import the new UI module
from src.ui.bubble import StatusBubble
# Import AppKit to run blocking updates on main thread if needed
import AppKit

class ErikSTTApp(rumps.App):
    def __init__(self):
        super(ErikSTTApp, self).__init__("ErikSTT", title="🎙️")
        
        # Initialize the STT engine
        self.stt = ErikSTT()
        
        # Initialize the Visual Feedback Bubble
        self.bubble = StatusBubble()
        
        # Override the STT state callbacks to update UI
        self.original_start = self.stt.start_recording
        self.original_stop = self.stt.stop_recording
        
        self.stt.start_recording = self.wrapped_start_recording
        self.stt.stop_recording = self.wrapped_stop_recording
        
        # Setup Menu
        self.setup_menu()
        
        # Start the hotkey listener in non-blocking mode
        self.stt.start_listener(blocking=False)
        
    def setup_menu(self):
        self.menu = [
            rumps.MenuItem("Status: Idle"),
            rumps.separator,
            rumps.MenuItem("Mode: Raw", callback=self.toggle_mode),
            rumps.separator,
            # Quit is added automatically by rumps, but we can customize if needed
        ]
        
        # Set initial checkmark for mode
        self.update_mode_display()

    def update_mode_display(self):
        """Update the mode menu item text/state."""
        mode_item = self.menu["Mode: Raw"]
        if self.stt.mode == "raw":
            mode_item.title = "Mode: Raw (Mode A)"
        else:
            mode_item.title = "Mode: Formatted (Mode B)"

    def toggle_mode(self, sender):
        """Toggle between Raw and Formatted modes."""
        if self.stt.mode == "raw":
            self.stt.mode = "formatted"
        else:
            self.stt.mode = "raw"
        
        self.update_mode_display()
        print(f"Mode switched to: {self.stt.mode}")

    def wrapped_start_recording(self):
        """Wrapper to update UI when recording starts."""
        # Call original method
        self.original_start()
        
        # Update UI
        self.title = "🔴 Recording..."
        self.menu["Status: Idle"].title = "Status: Recording..."
        
        # Show Bubble
        self.bubble.show("🔴 Recording...")

    def wrapped_stop_recording(self):
        """Wrapper to update UI when recording stops."""
        # Update UI first to show processing
        self.title = "🧠 Transcribing..."
        self.menu["Status: Idle"].title = "Status: Transcribing..."
        
        # Update Bubble
        self.bubble.show("🧠 Transcribing...")
        
        # Run processing in a separate thread so we don't block the UI
        threading.Thread(target=self.run_processing_thread).start()

    def run_processing_thread(self):
        """Run the blocking processing logic in a background thread."""
        # This blocks for ~5s while Whisper runs
        # We pass self.bubble.hide as a callback so it runs BEFORE text injection
        self.original_stop(on_transcription_complete=self.bubble.hide)
        
        # Reset UI on the main thread
        # Note: self.title update is theoretically unsafe from background thread in standard Cocoa/PyObjC
        # but rumps seems to handle it or tolerate it. 
        
        # Reset Menubar
        self.title = "🎙️"
        self.menu["Status: Idle"].title = "Status: Idle"
        
        # Bubble is already hidden by the callback passed to original_stop

if __name__ == "__main__":
    # Run the app
    ErikSTTApp().run()
