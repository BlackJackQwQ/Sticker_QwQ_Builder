import sys
import os
from pathlib import Path

# ==============================================================================
#   STICKER MANAGER ENTRY POINT
# ==============================================================================
# This script acts as the launcher. It sets up the environment and starts the UI.

def launch_app():
    # 1. Configure Python Path
    # This ensures that imports work correctly regardless of where the script is run from.
    # It adds the directory containing Main.py to sys.path.
    base_path = Path(__file__).resolve().parent
    if str(base_path) not in sys.path:
        sys.path.append(str(base_path))

    # 2. Import Main Window
    # We import here (inside the function) to ensure paths are set up first.
    # Note: We are importing from 'UI.MainWindow' which corresponds to 'UI/MainWindow.py'
    try:
        from UI.MainWindow import StickerBotApp
    except ImportError as e:
        print("\nCRITICAL ERROR: Could not import the application UI.")
        print(f"Error Details: {e}")
        print("\nMake sure your folder structure looks like this:")
        print("  Sticker_Manager/")
        print("  ├── Main.py")
        print("  └── UI/")
        print("      └── MainWindow.py")
        input("Press Enter to exit...")
        return

    # 3. Start Application
    app = StickerBotApp()
    app.mainloop()

if __name__ == "__main__":
    launch_app()