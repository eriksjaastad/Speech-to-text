import AppKit
from Foundation import NSObject, NSMakeRect, NSColor, NSFont

class NonActivatingPanel(AppKit.NSPanel):
    """A panel that refuses to become the key window (prevents focus stealing)."""
    def canBecomeKeyWindow(self):
        return False
    
    def canBecomeMainWindow(self):
        return False
    
    def acceptsFirstResponder(self):
        return False
    
    def worksWhenModal(self):
        return True

class StatusBubble:
    """
    A native macOS floating bubble window using PyObjC (AppKit).
    """
    def __init__(self):
        # Create the panel (window)
        # Style mask: Borderless + NonactivatingPanel
        style = AppKit.NSWindowStyleMaskBorderless | AppKit.NSWindowStyleMaskNonactivatingPanel
        
        # Geometry (will center later)
        rect = NSMakeRect(0, 0, 250, 60)
        
        self.window = NonActivatingPanel.alloc().initWithContentRect_styleMask_backing_defer_(
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

    def _show_on_main(self, text):
        """Internal method to run on main thread."""
        self.label.setStringValue_(text)
        self.move_to_center()
        self.window.orderFront_(None)

    def show(self, text):
        """Show the bubble with text (Thread-safe)."""
        # Dispatch to main thread
        from PyObjCTools import AppHelper
        AppHelper.callAfter(self._show_on_main, text)

    def _hide_on_main(self):
        """Internal method to run on main thread."""
        self.window.orderOut_(None)

    def hide(self):
        """Hide the bubble (Thread-safe)."""
        from PyObjCTools import AppHelper
        AppHelper.callAfter(self._hide_on_main)
