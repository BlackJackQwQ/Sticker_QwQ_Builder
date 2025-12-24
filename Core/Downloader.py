import threading
import random
import unicodedata
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Local Imports
from Core.Config import logger, LIBRARY_FOLDER, BASE_DIR

class DownloadManager:
    """
    Handles the background download queue for Sticker Packs.
    Runs on a separate thread to keep the UI responsive.
    """

    def __init__(self, app_instance):
        self.app = app_instance # Reference to main app (to access client/library)
        self.queue: List[Dict[str, Any]] = []
        self.is_running: bool = False
        
        # Queue Statistics
        self.total_packs_queued: int = 0
        self.packs_processed: int = 0

    def add_to_queue(self, url_or_data: Any, type_: str = "new"):
        """
        Adds a task to the download queue.
        type_: 'new' (URL string) or 'update' (Pack Data Dict)
        """
        self.queue.append({"type": type_, "payload": url_or_data})
        self.total_packs_queued += 1
        
        if not self.is_running:
            self.start_worker()

    def start_worker(self):
        """Starts the background thread."""
        self.is_running = True
        threading.Thread(target=self._worker_loop, daemon=True).start()

    def _worker_loop(self):
        """Main loop that processes the queue."""
        # Import UI helpers inside thread to avoid circular imports during startup
        # (This is safe because _worker_loop runs after App init)
        
        while self.queue:
            self.packs_processed += 1
            task = self.queue.pop(0)
            
            # Create a prefix like "[Pack 1/5]"
            queue_status = f"[Pack {self.packs_processed}/{self.total_packs_queued}]"
            
            try:
                if task["type"] == "new":
                    self._process_new_pack(task["payload"], queue_status)
                elif task["type"] == "update":
                    self._process_existing_pack(task["payload"], queue_status)
            except Exception as e:
                # CRITICAL FIX: Log the full error stack trace for debugging
                logger.error(f"Critical Queue Worker Error: {e}", exc_info=True)
                self._safe_toast("Queue Error", f"Process failed: {str(e)}")
        
        # Finished Batch
        self.is_running = False
        self.packs_processed = 0
        self.total_packs_queued = 0
        self._safe_status("Idle")

    # ==========================================================================
    #   TASK HANDLERS
    # ==========================================================================

    def _process_new_pack(self, url: str, prefix: str):
        """Step 1: Fetch Metadata -> Step 2: Download Files"""
        self._safe_status(f"{prefix} Fetching Metadata: {url}")
        
        try:
            # 1. Fetch Metadata via Backend
            data = self.app.client.get_pack_by_name(url)
            
            if not data:
                logger.warning(f"Metadata fetch failed for URL: {url}")
                self._safe_toast("Failed", f"Invalid Pack or API Error: {url}")
                return

            # 2. Check Duplicates
            # Using 't_name' (telegram unique name) to prevent duplicate folders
            if any(p.get('t_name') == data.get('name') for p in self.app.library_data):
                logger.info(f"Pack already exists: {data.get('name')}")
                self._safe_toast("Skipped", f"Already exists: {data.get('title')}")
                return

            # 3. Create Database Entry
            new_pack = {
                "name": data["title"], 
                "count": len(data["stickers"]), 
                "color": "gray",
                "t_name": data["name"], 
                "url": f"t.me/addstickers/{data['name']}",
                "stickers": data["stickers"], 
                "added": datetime.now().strftime("%Y-%m-%d"),
                "updated": datetime.now().strftime("%Y-%m-%d"), 
                "downloaded": False, 
                "tags": [], 
                "is_favorite": False, 
                "linked_packs": []
            }
            
            # Auto-tagging based on Emoji
            for s in new_pack['stickers']:
                s['tags'] = []
                emoji = s.get('emoji')
                if emoji:
                    emoji = emoji.strip()
                    try:
                        name = unicodedata.name(emoji[0]).title()
                        tag_str = f"{emoji} - {name}"
                    except Exception:
                        tag_str = emoji 
                    s['tags'].append(tag_str)
                s['usage_count'] = 0
                s['is_favorite'] = False

            # Add to Library immediately
            # NOTE: Thread-safety is now handled by Core.Config.save_json lock
            self.app.library_data.append(new_pack)
            self.app.client.save_library(self.app.library_data)
            
            # Refresh UI (Thread-Safe Call)
            self.app.after(0, self.app.refresh_view)
            
            # 4. Download Content
            self._process_existing_pack(new_pack, prefix)

        except Exception as e:
            logger.error(f"Error processing new pack '{url}': {e}", exc_info=True)
            self._safe_toast("Error", f"Failed to add pack: {url}")

    def _process_existing_pack(self, pack_obj: Dict[str, Any], prefix: str):
        """Downloads the actual images for a known pack object."""
        name = pack_obj.get('name', 'Unknown')
        t_name = pack_obj.get('t_name', 'Unknown')
        
        try:
            # Custom callback to show "Pack X/Y" AND "Sticker A/B"
            def update_prog(curr, total):
                pct = curr / total if total > 0 else 0
                msg = f"{prefix} Downloading '{name}': Sticker {curr}/{total}"
                self._safe_status(msg, pct)

            # Call the heavy network function in Backend
            path = self.app.client.download_pack(t_name, pack_obj['stickers'], progress_callback=update_prog)
            
            if not path:
                 logger.error(f"Download returned no path for {t_name}")
                 self._safe_toast("Error", f"Download failed for {name}")
                 return
                 
            pack_obj['downloaded'] = True
            
            # Post-Process: Check file types to tag 'Static' vs 'Animated'
            path_obj = Path(path)
            if path_obj.exists():
                for i, s in enumerate(pack_obj['stickers']):
                    webp_p = path_obj / f"sticker_{i}.webp"
                    gif_p = path_obj / f"sticker_{i}.gif"
                    
                    if webp_p.exists():
                        if "Static" not in s['tags']: s['tags'].append("Static")
                    elif gif_p.exists():
                         if "Animated" not in s['tags']: s['tags'].append("Animated")

                # Set Thumbnail if missing
                if not pack_obj.get('thumbnail_path'):
                    valid_exts = {'.png', '.gif', '.webp'}
                    try:
                        imgs = [p.name for p in path_obj.iterdir() if p.suffix.lower() in valid_exts]
                        if imgs: 
                            pack_obj['temp_thumbnail'] = str(path_obj / random.choice(imgs))
                    except Exception as e:
                        logger.warning(f"Thumbnail selection error: {e}")

            self.app.client.save_library(self.app.library_data)
            
            # Finalize
            self._safe_toast("Complete", f"Ready: {name}")
            
            # Refresh logic
            self.app.after(0, lambda: self.app.logic.apply_filters())
            self.app.after(0, self.app.refresh_view)

        except Exception as e:
            logger.error(f"Error downloading pack '{name}': {e}", exc_info=True)
            self._safe_toast("Error", f"Download crashed for {name}")

    # ==========================================================================
    #   THREAD-SAFE UI HELPERS
    # ==========================================================================
    
    def _safe_toast(self, title, msg):
        # Import inside function to prevent circular dependency
        from UI.ViewUtils import ToastNotification
        self.app.after(0, lambda: ToastNotification(self.app, title, msg))

    def _safe_status(self, msg, progress=None):
        self.app.after(0, lambda: self.app.update_status_bar(msg, progress))