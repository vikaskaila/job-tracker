"""
Build script to create executable using PyInstaller
Run: python build.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build executable with PyInstaller"""
    
    print("=" * 60)
    print("Job Tracker - PyInstaller Build Script")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("\n❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Get system platform
    import platform
    system = platform.system()
    
    print(f"\n📦 Building for {system}...")
    
    # Base PyInstaller command
    base_cmd = [
        "pyinstaller",
        "--name=JobTracker",
        "--onefile",
        "--windowed",
        "--clean",
    ]
    
    # Add hidden imports
    hidden_imports = [
        "jobspy",
        "schedule",
        "googleapiclient",
        "google_auth_oauthlib",
        "google_auth_httplib2",
        "fuzzywuzzy",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets"
    ]
    
    for imp in hidden_imports:
        base_cmd.extend(["--hidden-import", imp])
    
    # Add data files
    if os.path.exists("credentials.json"):
        base_cmd.extend(["--add-data", "credentials.json:."])
    
    if os.path.exists("config.json"):
        base_cmd.extend(["--add-data", "config.json:."])
    
    # Platform-specific options
    if system == "Windows":
        # Try to find and use an icon
        if os.path.exists("icon.ico"):
            base_cmd.extend(["--icon", "icon.ico"])
        base_cmd.append("main.py")
        
    elif system == "Darwin":  # macOS
        if os.path.exists("icon.icns"):
            base_cmd.extend(["--icon", "icon.icns"])
        base_cmd.append("main.py")
        
    else:  # Linux
        if os.path.exists("icon.png"):
            base_cmd.extend(["--icon", "icon.png"])
        base_cmd.append("main.py")
    
    print("\n📋 Build Command:")
    print(" ".join(base_cmd))
    print("\n")
    
    # Run PyInstaller
    try:
        result = subprocess.run(base_cmd, check=True)
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            
            # Get executable path
            if system == "Windows":
                exe_path = os.path.join("dist", "JobTracker.exe")
            else:
                exe_path = os.path.join("dist", "JobTracker")
            
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📦 Executable created: {exe_path} ({file_size:.1f} MB)")
                print(f"\n🚀 To run the application:")
                print(f"   - Windows: double-click JobTracker.exe")
                print(f"   - Mac/Linux: ./dist/JobTracker")
            else:
                print(f"⚠️ Could not find executable at {exe_path}")
        else:
            print(f"\n❌ Build failed with return code {result.returncode}")
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build error: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ PyInstaller not found. Make sure it's installed:")
        print("   pip install pyinstaller")
        return False
    
    return True

def cleanup():
    """Clean up build artifacts"""
    print("\n🧹 Cleaning up build files...")
    
    # Remove build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
        print("   Removed build/")
    
    # Remove .spec file
    if os.path.exists("JobTracker.spec"):
        os.remove("JobTracker.spec")
        print("   Removed JobTracker.spec")
    
    print("✅ Cleanup complete!")

def create_installer_script():
    """Create a helpful launcher script"""
    
    print("\n📝 Creating launcher scripts...")
    
    # Windows batch file
    if os.path.exists(os.path.join("dist", "JobTracker.exe")):
        with open("run_job_tracker.bat", "w") as f:
            f.write("@echo off\n")
            f.write("cd /d %~dp0\n")
            f.write("dist\\JobTracker.exe\n")
        print("   Created run_job_tracker.bat (Windows)")
    
    # Unix shell script
    if os.path.exists(os.path.join("dist", "JobTracker")):
        with open("run_job_tracker.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("./dist/JobTracker\n")
        os.chmod("run_job_tracker.sh", 0o755)
        print("   Created run_job_tracker.sh (Mac/Linux)")

if __name__ == "__main__":
    success = build_executable()
    
    if success:
        cleanup()
        create_installer_script()
        print("\n" + "=" * 60)
        print("✅ Build Process Complete!")
        print("=" * 60)
        print("\n📌 Next Steps:")
        print("   1. Ensure all dependencies are included in dist/")
        print("   2. Test the executable thoroughly")
        print("   3. Create an installer or zip for distribution")
        print("\n")
    else:
        print("\n" + "=" * 60)
        print("❌ Build Failed")
        print("=" * 60)
        sys.exit(1)
