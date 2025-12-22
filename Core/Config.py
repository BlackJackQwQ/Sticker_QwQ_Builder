import json
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Union

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
#   DEFAULT SETTINGS
# ==============================================================================
DEFAULT_SETTINGS: Dict[str, Any] = {
    "token": "",
    "theme_name": "Classic", 
    "nsfw_enabled": False,
    "show_favorites_only": False,
    "custom_theme_data": {} 
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
        
    if not os.path.exists(LIBRARY_FILE):
        save_json([], LIBRARY_FILE)

# ==============================================================================
#   IO HELPERS
# ==============================================================================

def save_json(data: Any, filename: str):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")

def load_json(filename: str) -> Any:
    if not os.path.exists(filename): return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}