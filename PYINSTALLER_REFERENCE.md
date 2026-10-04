# PyInstaller Build Commands - Complete Reference

This file contains all PyInstaller commands needed to build the Job Tracker as an executable for different platforms.

## 🚀 Quick Build (Recommended)

The easiest way - just run:

```powershell
python build.py
```

This automated script handles everything and creates `dist/JobTracker.exe` on Windows.

---

## 🪟 Windows - Detailed Commands

### Basic Build (Single EXE)
```powershell
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            main.py
```

### With All Options (Recommended)
```powershell
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --hidden-import=jobspy `
            --hidden-import=schedule `
            --hidden-import=googleapiclient `
            --hidden-import=google_auth_oauthlib `
            --hidden-import=google_auth_httplib2 `
            --hidden-import=fuzzywuzzy `
            --hidden-import=PyQt6.QtCore `
            --hidden-import=PyQt6.QtGui `
            --hidden-import=PyQt6.QtWidgets `
            main.py
```

### With Icon (Professional)
```powershell
# First, prepare an icon.ico file (256x256 or larger)
# Then run:

pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --icon=icon.ico `
            --hidden-import=jobspy `
            --hidden-import=schedule `
            --hidden-import=googleapiclient `
            --hidden-import=google_auth_oauthlib `
            --hidden-import=google_auth_httplib2 `
            --hidden-import=fuzzywuzzy `
            --hidden-import=PyQt6.QtCore `
            --hidden-import=PyQt6.QtGui `
            --hidden-import=PyQt6.QtWidgets `
            --distpath dist `
            --buildpath build `
            main.py
```

### With Debug Output
```powershell
# Shows all PyInstaller processing steps

pyinstaller --debug=imports `
            --name "JobTracker" `
            --onefile `
            --windowed `
            --hidden-import=jobspy `
            main.py
```

### Clean Build
```powershell
# Remove old build artifacts first

Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "JobTracker.spec" -Force -ErrorAction SilentlyContinue

# Then build fresh
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --hidden-import=jobspy `
            main.py
```

---

## 🍎 macOS - Build Commands

### Basic Build
```bash
pyinstaller --name "JobTracker" \
            --onefile \
            --windowed \
            main.py
```

### Full Build with Icon
```bash
# Prepare icon.icns file first

pyinstaller --name "JobTracker" \
            --onefile \
            --windowed \
            --icon=icon.icns \
            --hidden-import=jobspy \
            --hidden-import=schedule \
            --hidden-import=googleapiclient \
            --hidden-import=google_auth_oauthlib \
            --hidden-import=google_auth_httplib2 \
            --hidden-import=fuzzywuzzy \
            --hidden-import=PyQt6.QtCore \
            --hidden-import=PyQt6.QtGui \
            --hidden-import=PyQt6.QtWidgets \
            main.py
```

### Creating .dmg (Installer)
```bash
# After building:
hdiutil create -volname "Job Tracker" -srcfolder dist -ov -format UDZO JobTracker.dmg
```

### Make Executable
```bash
chmod +x dist/JobTracker
```

---

## 🐧 Linux - Build Commands

### Ubuntu/Debian
```bash
# Install dependencies first:
sudo apt-get install libqt6core6 libqt6gui6 libqt6widgets6

# Build
pyinstaller --name JobTracker \
            --onefile \
            --windowed \
            --hidden-import=jobspy \
            --hidden-import=schedule \
            --hidden-import=googleapiclient \
            --hidden-import=google_auth_oauthlib \
            --hidden-import=google_auth_httplib2 \
            --hidden-import=fuzzywuzzy \
            --hidden-import=PyQt6.QtCore \
            --hidden-import=PyQt6.QtGui \
            --hidden-import=PyQt6.QtWidgets \
            main.py
```

### Make Executable
```bash
chmod +x dist/JobTracker
```

### Create AppImage (Shareable)
```bash
# Requires appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage dist/JobTracker JobTracker.AppImage
```

---

## 🔍 Understanding PyInstaller Options

### Key Flags Explained

```
--name "JobTracker"           # Executable name
--onefile                     # Single file (vs folder)
--windowed                    # No console window
--icon=path.ico              # Icon file for executable
--hidden-import=module        # Force include module
--distpath dist              # Output folder
--buildpath build            # Build folder
--debug=imports              # Debug mode
--clean                      # Clean build first
--noupx                      # Don't compress with UPX
--add-data src:dst          # Add data files
```

### Hidden Imports (Why Needed)

These packages need explicit inclusion because PyInstaller can't detect them dynamically:

```python
jobspy                  # Job scraping library
schedule               # Background scheduling
googleapiclient        # Gmail API
google_auth_oauthlib   # Google OAuth
google_auth_httplib2   # Google HTTP client
fuzzywuzzy            # Fuzzy string matching
PyQt6.*               # Qt GUI modules
```

---

## ✅ Verification Checklist

After building, verify with:

### Windows
```powershell
# File should exist
Test-Path "dist/JobTracker.exe"

# Check size (should be 80-120 MB)
(Get-Item "dist/JobTracker.exe").Length / 1MB

# Test run
.\dist\JobTracker.exe
```

### macOS/Linux
```bash
# File should exist
ls -lh dist/JobTracker

# Check size (should be 80-120 MB)
du -h dist/JobTracker

# Test run
./dist/JobTracker
```

---

## 🐛 Troubleshooting Build Issues

### Module Not Found Error
```
Error: Cannot find module 'X'
Solution: Add --hidden-import=X to command
```

Example:
```powershell
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --hidden-import=missing_module_name `
            main.py
```

### PyQt6 Import Error
```
Error: No module named 'PyQt6'
Solution: Ensure all Qt hidden imports included:
```

```powershell
--hidden-import=PyQt6.QtCore `
--hidden-import=PyQt6.QtGui `
--hidden-import=PyQt6.QtWidgets `
```

### Build Fails
```
Solution: Clean and rebuild:
```

```powershell
Remove-Item -Path "build", "dist", "*.spec" -Force -Recurse
python build.py
```

### Executable Won't Start
```
Check: python -m PyInstaller --version
Ensure: All dependencies installed (pip install -r requirements.txt)
Verify: main.py runs with Python directly
```

---

## 📊 Build Optimization

### Reduce File Size

Option 1: Use UPX Compression
```powershell
# Install UPX first
choco install upx  # Windows

# Then build without --noupx
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            main.py
```

Option 2: Exclude Unnecessary Modules
```powershell
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --exclude-module=numpy `
            --exclude-module=pandas `
            main.py
```

Option 3: Use Upx Manually
```powershell
upx --best dist/JobTracker.exe
```

### Reduce Build Time

Option 1: Skip Analysis
```powershell
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            --noconfirm `
            main.py
```

Option 2: Cache Previous Build
```powershell
# Keep build/ folder for incremental builds
pyinstaller --name "JobTracker" `
            --onefile `
            --windowed `
            main.py
```

---

## 📝 Build Script Contents

The automated `build.py` does this:

1. ✅ Detects your platform (Windows/Mac/Linux)
2. ✅ Checks PyInstaller installed
3. ✅ Adds all necessary hidden imports
4. ✅ Includes optional icon if available
5. ✅ Builds single executable
6. ✅ Cleans up build artifacts
7. ✅ Creates launcher scripts
8. ✅ Shows build summary

**Just run:** `python build.py`

---

## 🚀 Distribution Options

### Option 1: Direct EXE
```
Share: dist/JobTracker.exe
User: Double-click to run (no Python needed)
```

### Option 2: Compressed ZIP
```powershell
# Create zip
Compress-Archive -Path dist/JobTracker.exe -DestinationPath JobTracker.zip

# Share zip file
```

### Option 3: Installer (Windows)
```
# Use Inno Setup or NSIS
# Include JobTracker.exe
# Create shortcut to exe
# Include README.md, QUICKSTART.md
```

### Option 4: GitHub Release
```
1. Create GitHub repo
2. Upload exe to Releases
3. Share download link
4. Users download .exe and run
```

---

## 🔒 Code Signing (Optional - Professional)

For enterprise distribution, sign the executable:

### Windows Code Signing
```powershell
# Requires certificate
signtool sign /f certificate.pfx /p password /t http://timestamp.server dist/JobTracker.exe
```

### macOS Code Signing
```bash
codesign --deep --force --verify --verbose --sign - dist/JobTracker
```

---

## 📋 Complete Build Checklist

Before building:
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] main.py runs successfully: `python main.py`
- [ ] PyInstaller installed: `pip install pyinstaller`
- [ ] No syntax errors in code

Building:
- [ ] Run: `python build.py` (recommended)
- [ ] Or: Manually run appropriate command above
- [ ] Wait for completion (2-5 minutes)

After building:
- [ ] Check file exists: `dist/JobTracker.exe`
- [ ] Check file size (80-120 MB)
- [ ] Test by double-clicking
- [ ] Verify all features work
- [ ] Check database/config created

---

## 📞 Getting Help

### PyInstaller Documentation
- https://pyinstaller.readthedocs.io/

### Common Issues
- Check **DEPLOYMENT.md** for distribution help
- Check **REQUIREMENTS.md** for environment setup
- Check **troubleshooting** section above
- Review `job_tracker.log` if exe won't run

---

## 🎯 Quick Reference

**Want to build EXE?**
```powershell
python build.py
```

**Want to verify PyInstaller?**
```powershell
pyinstaller --version
```

**Want to find your EXE?**
```powershell
Get-ChildItem -Path "dist" -Name "*.exe"
```

**Want to test it?**
```powershell
.\dist\JobTracker.exe
```

---

## ✅ Summary

You have **three ways** to build:

1. **Automated (Easiest)**
   ```powershell
   python build.py
   ```

2. **Manual Windows**
   ```powershell
   # Copy exact command from Windows section above
   ```

3. **Manual Mac/Linux**
   ```bash
   # Copy exact command from macOS/Linux section above
   ```

All produce single `JobTracker` executable (~100 MB) that users can run without Python!

---

**Ready to build? Run:** `python build.py` 🚀
