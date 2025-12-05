import subprocess
import time

def get_active_app():
    """Get the name of the currently frontmost application."""
    try:
        res = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to name of first application process whose frontmost is true'],
            capture_output=True, 
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"⚠ Could not get active app: {e}")
        return None

def activate_app(app_name):
    """Activate (focus) a specific application by name."""
    if not app_name:
        return
        
    print(f"🔄 Restoring focus to: {app_name}")
    script = f'tell application "{app_name}" to activate'
    try:
        subprocess.run(["osascript", "-e", script], check=True)
        time.sleep(0.1) # Allow focus to settle
    except Exception as e:
        print(f"⚠ Could not activate app {app_name}: {e}")

def inject_text_applescript(text):
    """
    Inject text using AppleScript keystroke (fallback method).
    Types text character by character at cursor position.
    """
    # Escape special characters for AppleScript
    escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')

    script = f'''
    tell application "System Events"
        keystroke "{escaped}"
    end tell
    '''

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        print("✓ Text injected via AppleScript keystroke")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ AppleScript injection failed: {e}")
        return False

def inject_text_clipboard(text):
    """
    Inject text using clipboard + paste (primary method).
    Copies text to clipboard, then pastes with Cmd+V.
    """
    try:
        # Copy to clipboard
        subprocess.run(["pbcopy"], input=text.encode(), check=True)

        # Paste with Cmd+V
        time.sleep(0.2)  # Give clipboard a moment to update and app to be ready
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)
        print("✓ Text injected via clipboard paste (primary method)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Clipboard injection failed: {e}")
        return False

def inject_text(text, force_applescript=False, restore_app=None):
    """
    Inject text at cursor using primary clipboard method, fallback to AppleScript.
    
    Args:
        text: The text to inject
        force_applescript: If True, skip clipboard and use AppleScript directly (for testing)
        restore_app: Optional name of app to refocus before injection
    """
    # Restore focus if requested
    if restore_app:
        activate_app(restore_app)
        
    # If forcing AppleScript (for testing fallback), skip clipboard
    if force_applescript:
        print("⚠ Forcing AppleScript method (testing fallback)...")
        return inject_text_applescript(text)
    
    # Try clipboard method first (faster and more reliable)
    # Debug: Check active app
    current_app = get_active_app()
    if current_app:
        print(f"👀 Active App for Injection: {current_app}")

    if inject_text_clipboard(text):
        return True

    # Fall back to AppleScript keystroke (slower)
    print("⚠ Clipboard method failed, trying AppleScript keystroke...")
    return inject_text_applescript(text)

if __name__ == "__main__":
    import sys
    
    # Check if user wants to test fallback
    test_fallback = "--test-fallback" in sys.argv or "--applescript" in sys.argv
    
    # Test the injection
    test_text = "Hello from Erik STT! This is a test."
    
    if test_fallback:
        print("=" * 60)
        print("TESTING APPLESCRIPT FALLBACK (skipping clipboard)")
        print("=" * 60)
    else:
        print("=" * 60)
        print("TESTING PRIMARY CLIPBOARD METHOD")
        print("(Run with --test-fallback to test AppleScript instead)")
        print("=" * 60)
    
    print("\nInjecting text in 3 seconds... Focus Notes.app or any text editor now!")
    time.sleep(3)

    success = inject_text(test_text, force_applescript=test_fallback)
    
    print("\n" + "=" * 60)
    print(f"Final result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    print("=" * 60)
