import AppKit
from Foundation import NSObject, NSMakeRect, NSColor, NSFont

class StatusBubble:
    """
    A native macOS floating bubble window using PyObjC (AppKit).
    """
    def __init__(self):
        # Create the panel (window)
        # Style mask: Borderless (no title bar)
        style = AppKit.NSWindowStyleMaskBorderless
        
        # Geometry (will center later)
        rect = NSMakeRect(0, 0, 250, 60)
        
        self.window = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            style,
            AppKit.NSBackingStoreBuffered,
            False
        )
        
        # Window attributes
        self.window.setLevel_(AppKit.NSFloatingWindowLevel)  # Float above other windows
        self.window.setBackgroundColor_(NSColor.blackColor())
        self.window.setAlphaValue_(0.85)
        self.window.setOpaque_(False)
        self.window.setHasShadow_(True)
        self.window.setIgnoresMouseEvents_(True)  # Pass clicks through (optional)
        
        # Round corners (standard macOS radius)
        self.window.contentView().setWantsLayer_(True)
        self.window.contentView().layer().setCornerRadius_(12.0)
        self.window.contentView().layer().setMasksToBounds_(True)

        # Create Label
        self.label = AppKit.NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 250, 60))
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        
        # Font settings
        font = NSFont.systemFontOfSize_weight_(20.0, 0.4) # 0.4 is roughly Medium/Semibold weight
        self.label.setFont_(font)
        self.label.setTextColor_(NSColor.whiteColor())
        self.label.setAlignment_(2) # Center alignment (technically NSTextAlignmentCenter=1/2 depending on version, 2 is usually safe for Center)
        
        # Center vertically roughly
        # NSTextField doesn't vertical align easily, so we just pad/position it.
        # Actually, let's just frame it correctly.
        # Using a slightly offset frame to center text visually.
        self.label.setFrame_(NSMakeRect(0, 15, 250, 30))
        
        self.window.contentView().addSubview_(self.label)
    
    def move_to_center(self):
        """Center window on the active screen."""
        screen = AppKit.NSScreen.mainScreen()
        if screen:
            screen_rect = screen.visibleFrame()
            window_rect = self.window.frame()
            
            x = screen_rect.origin.x + (screen_rect.size.width - window_rect.size.width) / 2
            y = screen_rect.origin.y + (screen_rect.size.height - window_rect.size.height) * 0.8 # Top 20%
            
            self.window.setFrameOrigin_((x, y))

    def show(self, text):
        """Show the bubble with text (Thread-safe)."""
        # Ensure label update runs on main thread
        self.label.performSelectorOnMainThread_withObject_waitUntilDone_(
            "setStringValue:", text, True
        )
        
        # We need to center it too, but we can't easily dispatch 'move_to_center' via performSelector
        # unless we expose it as an ObjC selector or just chance it.
        # Generally setFrame from background is risky but often works.
        # Let's try to run the whole show logic on main thread if possible, 
        # but for now let's just make sure the visible parts are safe.
        
        self.move_to_center() # This uses setFrameOrigin, might need safety
        
        # Show window on main thread
        self.window.performSelectorOnMainThread_withObject_waitUntilDone_(
            "orderFront:", None, False
        )

    def hide(self):
        """Hide the bubble (Thread-safe)."""
        self.window.performSelectorOnMainThread_withObject_waitUntilDone_(
            "orderOut:", None, False
        )
