import threading
from typing import Union, List

from Core.Downloader import DownloadManager
from UI.ViewUtils import ToastNotification

class UpdateManager:
    """
    The Networker.
    Responsible for interfacing with the DownloadManager and checking for updates.
    """

    def __init__(self, app):
        self.app = app
        # Initialize the heavy-lifting Downloader (which runs in its own thread)
        self.downloader = DownloadManager(app)

    def add_pack_from_url(self, urls: Union[str, List[str]]):
        """
        Parses URLs or Pack Names and queues them for download.
        Handles both new packs and updates to existing ones.
        """
        # Security check: User must have a token to talk to Telegram
        if not self.app.client.token:
            self.app.popup_manager.open_settings_modal()
            return

        if isinstance(urls, str): urls = [urls]
        
        queued_count = 0
        existing_updated = False
        
        for url in urls:
            clean_url = url.strip()
            if not clean_url: continue
            
            # Extract simple name (e.g. from "t.me/addstickers/Name")
            potential_name = clean_url.split('/')[-1]
            
            # Check if we already have it
            existing = next((p for p in self.app.library_data if p['t_name'] == potential_name), None)
            
            if existing:
                self.downloader.add_to_queue(existing, "update")
                existing_updated = True
                # Notify per-pack only if singular, else wait for summary
                if len(urls) == 1:
                    ToastNotification(self.app, "Duplicate", f"Updating existing pack: {existing['name']}")
            else:
                self.downloader.add_to_queue(clean_url, "new")
                queued_count += 1
        
        # Summary Notification
        if queued_count > 0:
            ToastNotification(self.app, "Queue Started", f"Processing {len(urls)} packs")
        elif len(urls) > 1 and existing_updated:
            ToastNotification(self.app, "Updates Queued", "Refreshing existing packs.")

    def trigger_redownload(self):
        """Forces a re-download of the currently viewed pack."""
        if self.app.logic.current_pack_data:
            self.downloader.add_to_queue(self.app.logic.current_pack_data, "update")
            # SUCCESS NOTIFICATION HERE
            ToastNotification(self.app, "Queued", "Download Queued Successfully.")
            
    def update_all_packs(self):
        """Opens the update modal which runs _run_update_check."""
        self.app.popup_manager.open_update_modal(self._run_update_check)

    def _run_update_check(self, progress_callback, status_callback, finish_callback):
        """
        Background task to check every pack in the library against the Telegram API.
        If the sticker count differs, it queues an update.
        """
        def _check():
            total = len(self.app.library_data)
            updates_found = 0
            
            for i, pack in enumerate(self.app.library_data):
                if status_callback: 
                    status_callback(f"Checking: {pack.get('name')}")
                if progress_callback: 
                    progress_callback(i / total)
                
                try:
                    # Fetch remote metadata
                    remote = self.app.client.get_pack_by_name(pack.get('t_name'))
                    
                    # Compare counts (simple heuristic for updates)
                    if remote and len(remote.get('stickers', [])) != pack.get('count', 0):
                        # Update metadata immediately
                        pack['stickers'] = remote['stickers']
                        pack['count'] = len(remote['stickers'])
                        
                        # Queue for file download
                        self.downloader.add_to_queue(pack, "update")
                        updates_found += 1
                except Exception: 
                    pass
            
            if progress_callback: progress_callback(1.0)
            
            final_msg = f"Queued {updates_found} updates." if updates_found > 0 else "Library is up to date."
            if status_callback: status_callback(final_msg)
            
            # Close modal after delay
            self.app.after(1500, finish_callback)
            
        threading.Thread(target=_check, daemon=True).start()