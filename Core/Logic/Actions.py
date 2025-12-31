import random
import webbrowser
from datetime import datetime
from pathlib import Path

from Core.Config import BASE_DIR, LIBRARY_FOLDER
from UI.ViewUtils import copy_to_clipboard, open_file_location, resize_image_to_temp, ToastNotification

class ActionManager:
    """
    The Toolset.
    Responsible for interactions with the OS (Clipboard, Explorer, Browser)
    and transient selection actions (Random Sticker).
    """

    def __init__(self, app):
        self.app = app

    def copy_sticker(self):
        """Copies the currently selected sticker to the clipboard."""
        if not self.app.logic.selected_stickers: return
        
        # Get data from the last selected sticker
        data, _, path, _ = self.app.logic.selected_stickers[-1]
        if not path: return
        
        # Get requested size from UI (Detail Panel)
        # Note: Accessing UI state is necessary here as the user selects size in the view
        size_label = "Original"
        if hasattr(self.app, 'details_manager'):
            size_label = self.app.details_manager.sticker_layout.size_var.get()
        
        final_path = resize_image_to_temp(path, size_label)
        if final_path:
            copy_to_clipboard(final_path)
            
            # Update usage stats
            data['usage_count'] = data.get('usage_count', 0) + 1
            data['last_used'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.app.client.save_library(self.app.library_data)
            
            # Refresh if single selection to show updated stats immediately
            if len(self.app.logic.selected_stickers) == 1: 
                self.app.details_manager.update_details_panel()
            
            # SUCCESS NOTIFICATION with DETAILS
            sticker_name = data.get('custom_name', 'Sticker')
            ToastNotification(self.app, "Copied", f"'{sticker_name}' ({size_label}) copied to clipboard.")

    def show_file(self):
        """Opens the file explorer to the selected sticker's location."""
        if self.app.logic.selected_stickers: 
            open_file_location(self.app.logic.selected_stickers[-1][2], True)

    def open_url(self, e=None):
        """Opens the Telegram URL for the current pack."""
        if self.app.logic.current_pack_data: 
            webbrowser.open(self.app.logic.current_pack_data['url'])

    def select_random_sticker(self):
        """Selects a random sticker from the current view and highlights it."""
        source = self.app.filtered_stickers
        if not source: return
        
        choice = random.choice(source)
        # choice tuple: (sticker_data, pack_tname, index_in_pack)
        
        # Resolve full path
        base = BASE_DIR / LIBRARY_FOLDER / choice[1]
        final_path = None
        for ext in [".png", ".gif", ".webp"]:
            p = base / f"sticker_{choice[2]}{ext}"
            if p.exists(): 
                final_path = str(p); break
        
        # Update Logic State
        # Item format: (sticker_data, idx, path, pack_tname)
        item = (choice[0], choice[2], final_path, choice[1])
        
        self.app.logic.selected_stickers = [item]
        self.app.logic.current_sticker_data = choice[0]
        self.app.logic.current_sticker_path = final_path
        
        # Refresh UI to show the selection
        self.app.details_manager.update_details_panel()