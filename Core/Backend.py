import requests
import json
import time
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union

# --- UPDATED IMPORTS ---
from Core.Config import (
    LIBRARY_FILE, 
    LIBRARY_FOLDER, 
    BASE_DIR, 
    save_json, 
    load_json, 
    logger
)

class StickerClient:
    """
    The Backend Engine.
    
    This class handles all communication with the Telegram API.
    It is responsible for:
    1. Fetching sticker pack metadata.
    2. Downloading raw image files using MULTITHREADING.
    3. Converting/Saving to local library (.webp/.gif).
    4. Auto-tagging stickers.
    5. Managing the 'library.json' database file.
    """

    def __init__(self, token: str = ""):
        self.token = token
        self.base_url = ""
        self.file_base_url = ""
        self.session = requests.Session()
        
        if self.token:
            self.update_urls()

    # ==========================================================================
    #   CONFIGURATION
    # ==========================================================================

    def update_urls(self):
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{self.token}"

    def set_token(self, new_token: str):
        self.token = new_token
        self.update_urls()

    # ==========================================================================
    #   TELEGRAM API INTERACTION
    # ==========================================================================

    def get_pack_by_name(self, pack_name_or_url: str) -> Optional[Dict[str, Any]]:
        if not self.token:
            logger.error("No Bot Token provided in Settings.")
            return None

        clean_name = pack_name_or_url.strip()
        if "addstickers/" in clean_name:
            clean_name = clean_name.split("addstickers/")[-1]
        
        clean_name = clean_name.split("?")[0].strip("/")

        logger.info(f"Fetching pack info for ID: {clean_name}")

        try:
            response = self.session.get(f"{self.base_url}/getStickerSet", params={"name": clean_name}, timeout=10)
            data = response.json()
            
            if data.get("ok"):
                return data["result"]
            else:
                logger.warning(f"API Error for {clean_name}: {data.get('description')}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Network Connection Error: {e}")
            return None

    def download_pack(self, pack_name: str, stickers: List[Dict[str, Any]], progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[Path]:
        """
        Downloads every sticker in a list using MULTITHREADING.
        """
        if not self.token: return None

        # Prepare Local Folder
        base_path = BASE_DIR / LIBRARY_FOLDER / pack_name
        base_path.mkdir(parents=True, exist_ok=True)

        total = len(stickers)
        completed = 0
        logger.info(f"Starting PARALLEL download for '{pack_name}' ({total} stickers)...")
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for index, sticker in enumerate(stickers):
                futures.append(
                    executor.submit(self._download_single_sticker, sticker, index, base_path)
                )
            
            for future in as_completed(futures):
                try:
                    future.result()
                    completed += 1
                    if progress_callback: progress_callback(completed, total)
                except Exception as e:
                    logger.error(f"Thread Error: {e}")

        return base_path

    def _download_single_sticker(self, sticker: Dict[str, Any], index: int, base_path: Path):
        """Worker function to download and convert a single sticker."""
        try:
            file_id = sticker.get('file_id')
            if not file_id: return
            
            # A. Get link
            file_info_resp = self.session.get(f"{self.base_url}/getFile", params={"file_id": file_id}, timeout=10)
            file_info = file_info_resp.json()
            
            if not file_info.get("ok"): return
                
            remote_file_path = file_info['result']['file_path']
            download_url = f"{self.file_base_url}/{remote_file_path}"
            
            # B. Download bytes
            img_response = self.session.get(download_url, timeout=15)
            if img_response.status_code != 200: return

            # --- CRITICAL FIX START: Handle special formats directly ---
            if 'tags' not in sticker: sticker['tags'] = []

            # 1. TGS (Telegram Animated Sticker - Lottie JSON)
            if remote_file_path.endswith(".tgs"):
                output_path = base_path / f"sticker_{index}.tgs"
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                if "Animated" not in sticker['tags']: sticker['tags'].append("Animated")
                return # Stop processing, PIL cannot open this

            # 2. WebM (Video Sticker)
            if remote_file_path.endswith(".webm"):
                output_path = base_path / f"sticker_{index}.webm"
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                if "Video" not in sticker['tags']: sticker['tags'].append("Video")
                return # Stop processing, PIL cannot open this
            # --- CRITICAL FIX END ---

            img_data = BytesIO(img_response.content)
            
            # C. Save Standard Images (WebP, JPG, PNG)
            is_animated = getattr(sticker, "is_animated", False)
            
            with Image.open(img_data) as image:
                if is_animated:
                    output_path = base_path / f"sticker_{index}.gif"
                    if "Animated" not in sticker['tags']: sticker['tags'].append("Animated")
                    
                    if image.format != 'GIF':
                        try: image.save(output_path, "GIF", save_all=True, loop=0)
                        except: 
                            # Fallback if conversion fails
                            with open(output_path, 'wb') as f: f.write(img_response.content)
                    else:
                        image.save(output_path)
                else:
                    output_path = base_path / f"sticker_{index}.webp"
                    if "Static" not in sticker['tags']: sticker['tags'].append("Static")
                    image.save(output_path, "WEBP", quality=90, method=6)
                
        except Exception as e:
            logger.error(f"Error processing sticker {index} (ID: {sticker.get('file_id')}): {e}")

    # ==========================================================================
    #   DATABASE HELPER
    # ==========================================================================

    def save_library(self, data: List[Dict[str, Any]], filename: str = LIBRARY_FILE):
        save_json(data, filename)

    def load_library(self, filename: str = LIBRARY_FILE) -> List[Dict[str, Any]]:
        data = load_json(filename)
        return data if isinstance(data, list) else []