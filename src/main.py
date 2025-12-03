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
from pynput import keyboard
import scipy.io.wavfile as wav

# Package imports (run with: python -m src.main)
from src.engine import WhisperEngine, load_settings, load_vocab
from src.post_process import load_replacements, process_mode_a, process_mode_b
from src.injection import inject_text


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
        self.stream = None
        
        # Track currently pressed keys for Option+Space hotkey (toggle mode)
        self.pressed_keys = set()
        
        print("\n✓ Initialization complete!")
        print("=" * 60)
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream - appends audio chunks."""
        if status:
            print(f"⚠ Audio callback status: {status}")
        
        # Append audio chunk to our buffer
        self.audio_data.append(indata.copy())
    
    def start_recording(self):
        """Start recording audio from microphone."""
        if self.is_recording:
            return  # Already recording
        
        # Clear previous audio data
        self.audio_data = []
        self.is_recording = True
        
        # Create and start audio stream
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self.audio_callback
        )
        self.stream.start()
        
        print("🎤 Recording...")
    
    def stop_recording(self):
        """Stop recording and process the audio."""
        if not self.is_recording:
            return  # Not recording
        
        # Stop the stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.is_recording = False
        print("⏹ Stopped")
        
        # Process the recorded audio
        self.process_audio()
    
    def process_audio(self):
        """Transcribe, process, and inject the recorded audio."""
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
                
                # Inject text using clipboard-first method with AppleScript fallback
                print("💉 Injecting text...")
                success = inject_text(processed_text)
                
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
            # Clear the set to prevent repeat triggers while keys are held
            self.pressed_keys.clear()
            
            if self.is_recording:
                # Already recording → stop and transcribe
                self.stop_recording()
            else:
                # Not recording → start recording
                self.start_recording()
    
    def on_press(self, key):
        """Handle key press events."""
        # Add key to pressed set
        normalized = self._normalize_key(key)
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
    
    def run(self):
        """Start the application and listen for hotkeys."""
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
        
        # Start keyboard listener
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as listener:
            listener.join()
        
        print("✓ Application stopped")


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
