import customtkinter as ctk
from typing import Optional

from UI.ViewUtils import COLORS, center_window, set_window_icon

class BasePopUp:
    """
    Base class for all Popup sub-managers.
    Provides access to the main App instance and shared window creation logic.
    """
    def __init__(self, app):
        self.app = app

    def _create_base_window(self, title: str, width: int, height: int) -> ctk.CTkToplevel:
        """
        Creates a standard modal window with the correct theme, icon, and centering.
        """
        win = ctk.CTkToplevel(self.app)
        win.title(title)
        win.geometry(f"{width}x{height}")
        
        # Apply standard UI utilities
        center_window(win, width, height)
        set_window_icon(win)
        
        # Modal behavior
        win.attributes('-topmost', True)
        win.grab_set() 
        
        # Theme application
        win.configure(fg_color=COLORS["bg_main"])
        
        return win