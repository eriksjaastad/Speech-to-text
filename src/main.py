#!/usr/bin/env python3
"""
Erik's Personal Speech-to-Text Tool - Main Application
Hotkey-driven transcription with custom vocabulary and text injection.

Run with: python -m src.main
"""

import sounddevice as sd
import numpy as np
import tempfile
import time
from pathlib import Path
from collections import deque
from pynput import keyboard
import scipy.io.wavfile as wav

# Package imports (run with: python -m src.main)
from src.engine import WhisperEngine, load_settings, load_vocab
from src.post_process import load_replacements, process_mode_a, process_mode_b
from src.injection import inject_text, get_active_app


class ErikSTT:
    """Main Speech-to-Text application with hotkey control."""
    
    def __init__(self):
        """Initialize the STT engine and load configurations."""
        print("=" * 60)
        print("INITIALIZING ERIK STT")
        print("=" * 60)
        
        # Set up paths relative to project root
        project_root = Path(__file__).resolve().parent.parent
        vocab_path = project_root / "config" / "vocab.yaml"
        replacements_path = project_root / "config" / "replacements.yaml"
        settings_path = project_root / "config" / "settings.yaml"
        
        # Load settings first
        print(f"\n⚙️  Loading settings from {settings_path}...")
        self.settings = load_settings(str(settings_path))
        
        # Get processing mode from settings (default: "raw")
        self.mode = self.settings.get("modes", {}).get("default", "raw")
        print(f"   Processing mode: {self.mode}")
        
        # Load vocab and replacements
        print(f"\n📚 Loading vocabulary from {vocab_path}...")
        self.custom_vocab = load_vocab(str(vocab_path))
        print(f"   Loaded {len(self.custom_vocab)} custom terms")
        
        print(f"\n🔄 Loading replacements from {replacements_path}...")
        self.replacements = load_replacements(str(replacements_path))
        print(f"   Loaded {len(self.replacements)} replacement rules")
        
        # Initialize Whisper engine with settings from config
        print("\n🤖 Initializing Whisper Engine...")
        self.engine = WhisperEngine(config=self.settings)
        
        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 16000
        
        # Pre-roll buffer to capture audio before hotkey press (0.5s)
        # Assuming ~100ms chunks (conservative), 10 chunks = 1s. 
        # We'll use a larger buffer to be safe, exact duration depends on callback blocksize.
        self.pre_roll_buffer = deque(maxlen=20) 
        
        # Start persistent stream (eliminates startup latency)
        print("\n🎤 Starting persistent audio stream...")
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()
        
        # Track currently pressed keys for Option+Space hotkey (toggle mode)
        self.pressed_keys = set()
        
        # Track target app for injection
        self.target_app = None
        
        print("\n✓ Initialization complete!")
        print("=" * 60)
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream - appends audio chunks."""
        if status:
            pass # print(f"⚠ Audio callback status: {status}")
        
        # Only append if recording active
        if self.is_recording:
            self.audio_data.append(indata.copy())
        else:
            # Keep filling pre-roll buffer when not recording
            self.pre_roll_buffer.append(indata.copy())
    
    def start_recording(self):
        """Start recording audio from microphone."""
        if self.is_recording:
            return  # Already recording
        
        # Clear previous audio data
        self.audio_data = []
        
        # Add pre-roll buffer contents to capture the start of speech
        if self.pre_roll_buffer:
            self.audio_data.extend(self.pre_roll_buffer)
            
        self.is_recording = True
        
        # Capture the active app immediately when recording starts
        self.target_app = get_active_app()
        print(f"🎯 Target App: {self.target_app}")
        
        print("🎤 Recording...")
    
    def stop_recording(self, **kwargs):
        """Stop recording and process the audio."""
        if not self.is_recording:
            return  # Not recording
        
        # Wait a moment to capture the tail of the audio
        time.sleep(0.5)
        
        self.is_recording = False
        print("⏹ Stopped")
        
        # Process the recorded audio
        self.process_audio(**kwargs)
    
    def process_audio(self, on_transcription_complete=None):
        """
        Transcribe, process, and inject the recorded audio.
        
        Args:
            on_transcription_complete: Optional callback to run after transcription 
                                     but BEFORE injection (e.g., to hide UI).
        """
        if not self.audio_data:
            print("⚠ No audio data recorded")
            return
        
        start_time = time.time()
        
        try:
            # Concatenate all audio chunks
            audio_array = np.concatenate(self.audio_data, axis=0)
            
            # Flatten if needed
            if audio_array.ndim > 1:
                audio_array = audio_array.flatten()
            
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Convert to int16 for WAV
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wav.write(temp_path, self.sample_rate, audio_int16)
                
                print(f"💾 Saved audio to {temp_path}")
                
                # Debug: Audio Duration
                duration_sec = len(audio_array) / self.sample_rate
                print(f"⏱ Recorded Audio Duration: {duration_sec:.2f}s")
                
                # Transcribe with custom vocabulary
                print("🔊 Transcribing...")
                result = self.engine.transcribe(
                    temp_path,
                    language="en",
                    custom_vocab=self.custom_vocab
                )
                
                raw_text = result['text']
                print(f"📝 Raw transcription: {raw_text}")
                
                # Apply post-processing based on mode
                if self.mode == "raw":
                    processed_text = process_mode_a(raw_text, self.replacements)
                else:  # mode == "formatted"
                    processed_text = process_mode_b(raw_text, self.replacements)
                
                print(f"✨ Processed text: {processed_text}")
                
                # Run callback if provided (e.g., to hide bubble)
                if on_transcription_complete:
                    on_transcription_complete()
                
                # Inject text using clipboard-first method with AppleScript fallback
                # restore_app ensures focus is back on the target before pasting
                print("💉 Injecting text...")
                success = inject_text(processed_text, restore_app=self.target_app)
                
                if success:
                    print("✓ Text injection completed successfully")
                else:
                    print("✗ Text injection failed")
                
                # Calculate total latency
                total_time = time.time() - start_time
                print(f"⏱ Total latency: {total_time:.2f}s (inference: {result['inference_time']:.2f}s)")
                
        except Exception as e:
            print(f"✗ Error processing audio: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up temp file
            try:
                import os
                if 'temp_path' in locals():
                    os.unlink(temp_path)
                    print(f"🗑 Cleaned up {temp_path}")
            except Exception as e:
                print(f"⚠ Could not delete temp file: {e}")
    
    def _is_option_key(self, key):
        """Check if the key is Option (Alt) key."""
        return key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                       keyboard.Key.alt_gr)
    
    def _normalize_key(self, key):
        """Normalize key to a consistent representation."""
        # Normalize all Option variants to a single value
        if self._is_option_key(key):
            return 'option'
        return key
    
    def _check_hotkey(self):
        """Check if Option+Space hotkey is active and toggle recording."""
        if 'option' in self.pressed_keys and keyboard.Key.space in self.pressed_keys:
            if self.is_recording:
                # Already recording → stop and transcribe
                self.stop_recording()
            else:
                # Not recording → start recording
                self.start_recording()
    
    def on_press(self, key):
        """Handle key press events."""
        normalized = self._normalize_key(key)
        
        # Ignore key repeats (only process new presses)
        if normalized in self.pressed_keys:
            return
            
        # Add key to pressed set
        self.pressed_keys.add(normalized)
        
        # Check if Option+Space combo is complete
        self._check_hotkey()
    
    def on_release(self, key):
        """Handle key release events."""
        # Remove key from pressed set
        normalized = self._normalize_key(key)
        self.pressed_keys.discard(normalized)
        
        # Check for ESC to exit
        if key == keyboard.Key.esc:
            print("\n👋 Exiting...")
            return False  # Stop listener
    
    def start_listener(self, blocking=True):
        """Start the hotkey listener."""
        print("\n" + "=" * 60)
        print("ERIK STT - READY")
        print("=" * 60)
        print("\n📋 INSTRUCTIONS:")
        print("   • Press Option+Space to START recording")
        print("   • Press Option+Space again to STOP and transcribe")
        print("   • Press ESC to exit")
        print("   • Make sure target app is focused before stopping\n")
        print("Mode: {} (using {})".format(
            self.mode,
            "process_mode_a" if self.mode == "raw" else "process_mode_b"
        ))
        print("\nListening for hotkeys...\n")
        
        # Create listener
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()
        
        if blocking:
            self.listener.join()
            print("✓ Application stopped")

    def run(self):
        """Start the application in blocking mode (CLI)."""
        self.start_listener(blocking=True)


if __name__ == "__main__":
    try:
        app = ErikSTT()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
