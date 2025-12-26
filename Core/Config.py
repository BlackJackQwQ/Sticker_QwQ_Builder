import json
import os
import shutil
import logging
import threading
from pathlib import Path
from typing import Dict, Any

# ==============================================================================
#   LOGGING CONFIGURATION
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("StickerManager")

# ==============================================================================
#   FILE SYSTEM CONSTANTS
# ==============================================================================
BASE_DIR = Path.cwd()
SETTINGS_FILE  = "settings.json"
LIBRARY_FILE   = "library.json"
LIBRARY_FOLDER = "Library"
TEMP_FOLDER    = "Temp"

# ==============================================================================
#   THREAD SAFETY
# ==============================================================================
data_lock = threading.Lock()

# ==============================================================================
#   DEFAULT SETTINGS
# ==============================================================================
DEFAULT_SETTINGS: Dict[str, Any] = {
    "token": "",
    "theme_name": "Classic", 
    "nsfw_enabled": False,
    "show_favorites_only": False,
    "custom_theme_data": {},
    # Added for Phase 5: Storage for "All Stickers" and "Collection" covers
    "custom_covers": {
        "virtual_all_stickers": "",  # Path to cover for All Stickers
        # "collection_Name": "path/to/img"  <-- Dynamically added
    }
}

# ==============================================================================
#   SYSTEM INITIALIZATION
# ==============================================================================

def initialize_system_files():
    """Ensures all necessary folders and JSON files exist on startup."""
    # 1. Create Directories
    (BASE_DIR / LIBRARY_FOLDER).mkdir(exist_ok=True)
    
    # 2. Reset/Create Temp Folder
    temp_path = BASE_DIR / TEMP_FOLDER
    if temp_path.exists():
        try: shutil.rmtree(temp_path)
        except Exception as e: logger.warning(f"Could not clean temp folder: {e}")
    temp_path.mkdir(exist_ok=True)
    
    # 3. Create JSON files if missing
    if not os.path.exists(SETTINGS_FILE):
        save_json(DEFAULT_SETTINGS, SETTINGS_FILE)
    else:
        # MIGRATION: Ensure 'custom_covers' exists if loading old config
        try:
            current = load_json(SETTINGS_FILE)
            if "custom_covers" not in current:
                current["custom_covers"] = {}
                save_json(current, SETTINGS_FILE)
        except: pass
        
    if not os.path.exists(LIBRARY_FILE):
        save_json([], LIBRARY_FILE)

# ==============================================================================
#   IO HELPERS
# ==============================================================================

def save_json(data: Any, filename: str):
    """
    Thread-safe JSON saver.
    """
    try:
        with data_lock:
            temp_filename = f"{filename}.tmp"
            with open(temp_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            if os.path.exists(filename):
                os.replace(temp_filename, filename)
            else:
                os.rename(temp_filename, filename)
                
    except Exception as e:
        logger.error(f"CRITICAL: Error saving {filename}: {e}")
        if os.path.exists(f"{filename}.tmp"):
            try: os.remove(f"{filename}.tmp")
            except: pass

def load_json(filename: str) -> Any:
    if not os.path.exists(filename): return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}