import os
import subprocess
import sys
import shutil
import time
import importlib.util
from pathlib import Path

# Configuration
APP_NAME = "Sticker_QwQ_Manager"
MAIN_SCRIPT = "Main.py" 
# ADDED: opencv-python for WebM support
REQUIRED_PACKAGES = ['pyinstaller', 'customtkinter', 'pillow', 'requests', 'opencv-python']

def check_and_install_dependencies():
    print(f"\n{'='*50}")
    print("STEP 1: CHECKING DEPENDENCIES")
    print(f"{'='*50}")
    
    for package in REQUIRED_PACKAGES:
        # Handle import name differences (e.g., pillow -> PIL, opencv-python -> cv2)
        import_name = package
        if package == "pillow": import_name = "PIL"
        if package == "opencv-python": import_name = "cv2"
        
        if importlib.util.find_spec(import_name) is None:
            print(f"⚠️  '{package}' not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ '{package}' installed.")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install '{package}'. Please install it manually.")
                sys.exit(1)
        else:
            print(f"✅ '{package}' is ready.")

def clean_previous_builds():
    print(f"\n{'='*50}")
    print("STEP 2: CLEANING WORKSPACE")
    print(f"{'='*50}")
    
    dirs_to_clean = ["build", "dist"]
    files_to_clean = [f"{APP_NAME}.spec"]
    
    for d in dirs_to_clean:
        path = Path(d)
        if path.exists():
            print(f"🗑️  Removing directory: {d}")
            try: shutil.rmtree(path)
            except Exception as e: print(f"⚠️  Could not remove {d}: {e}")

    for f in files_to_clean:
        path = Path(f)
        if path.exists():
            print(f"🗑️  Removing file: {f}")
            try: path.unlink()
            except Exception as e: print(f"⚠️  Could not remove {f}: {e}")

def run_pyinstaller():
    print(f"\n{'='*50}")
    print("STEP 3: COMPILING EXECUTABLE")
    print(f"{'='*50}")

    # Check for Icon
    icon_path = Path('Assets') / 'Purple_Rose.ico'
    icon_arg = f"--icon={str(icon_path)}" if icon_path.exists() else ""

    # PyInstaller Command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        "--collect-all=customtkinter",
        # Add the Assets folder to the bundle
        f"--add-data=Assets{os.pathsep}Assets", 
        icon_arg,
        MAIN_SCRIPT
    ]
    
    # Filter empty args
    cmd = [arg for arg in cmd if arg]
    
    print("🚀 Launching PyInstaller...")
    try:
        subprocess.check_call(cmd)
        print("\n✅ Compilation Complete.")
    except subprocess.CalledProcessError:
        print("\n❌ Build Failed.")
        sys.exit(1)

def create_launcher():
    print(f"\n{'='*50}")
    print("STEP 4: FINALIZING")
    print(f"{'='*50}")
    
    dist_dir = Path("dist") / APP_NAME
    
    if os.name == 'nt': # Windows
        launcher_path = dist_dir / "PLAY.bat"
        try:
            with open(launcher_path, "w") as f:
                f.write('@echo off\n')
                f.write(f'start "" "{APP_NAME}.exe"\n')
                f.write('exit\n')
            print(f"✅ Created launcher: {launcher_path}")
        except Exception as e:
            print(f"⚠️  Could not create batch launcher: {e}")

    # Clean up the 'build' folder and spec file
    clean_path = Path("build")
    spec_path = Path(f"{APP_NAME}.spec")
    
    if clean_path.exists(): shutil.rmtree(clean_path)
    if spec_path.exists(): spec_path.unlink()
    
    print(f"\n🎉 BUILD SUCCESSFUL!")
    print(f"📂 Output Location: {dist_dir.absolute()}")

if __name__ == "__main__":
    check_and_install_dependencies()
    clean_previous_builds()
    run_pyinstaller()
    create_launcher()
    
    print("\nClosing in 5 seconds...")
    time.sleep(5)