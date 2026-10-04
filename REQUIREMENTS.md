# System Requirements & Installation Guide

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 7+ / macOS 10.12+ / Linux (any modern distro) |
| **RAM** | 512 MB (2 GB recommended) |
| **Disk Space** | 500 MB (for Python + all libraries) |
| **Internet** | Required (for job scraping + Gmail) |
| **Screen** | 1200x800 minimum resolution |

### Recommended

| Component | Recommended |
|-----------|-------------|
| **OS** | Windows 10/11, macOS 10.14+, Ubuntu 20.04+ |
| **RAM** | 4 GB or more |
| **Disk Space** | 2 GB free |
| **Browser** | Chrome, Firefox, Safari, or Edge (for job URLs) |

---

## 🔧 Installation Methods

### Method 1: Python Installation (Recommended for Developers)

#### Windows
1. Install Python 3.11+
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH"
   
2. Open PowerShell and verify:
   ```powershell
   python --version
   pip --version
   ```

3. Navigate to project folder:
   ```powershell
   cd f:\newJobScrappingTool
   ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. Run application:
   ```powershell
   python main.py
   ```

#### macOS
1. Install Python 3.11+
   ```bash
   brew install python@3.11
   ```

2. Navigate to project folder:
   ```bash
   cd /path/to/newJobScrappingTool
   ```

3. Create virtual environment (recommended):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run application:
   ```bash
   python main.py
   ```

#### Linux (Ubuntu/Debian)
1. Install Python 3.11+:
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3-pip
   ```

2. Install PyQt6 dependencies:
   ```bash
   sudo apt-get install libqt6core6 libqt6gui6 libqt6widgets6
   ```

3. Navigate to project folder:
   ```bash
   cd /path/to/newJobScrappingTool
   ```

4. Create virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Run application:
   ```bash
   python main.py
   ```

---

### Method 2: Executable Installation (No Python Required)

#### Windows (Easiest)
1. Download `JobTracker.exe` from distribution
2. Double-click to run
3. Application starts immediately
4. No installation needed

#### macOS
1. Download `JobTracker` application
2. Open Terminal and make executable:
   ```bash
   chmod +x /path/to/JobTracker
   ```
3. Double-click to run

#### Linux
1. Download `JobTracker` executable
2. Open terminal:
   ```bash
   chmod +x JobTracker
   ./JobTracker
   ```

---

## 📦 Dependencies Explained

### Core Libraries

| Package | Purpose | Version |
|---------|---------|---------|
| **PyQt6** | GUI framework | 6.6.1 |
| **jobspy** | Job scraping | 5.4.8 |
| **google-api-python-client** | Gmail API | 2.108.0 |
| **google-auth-oauthlib** | Google OAuth | 1.2.0 |
| **schedule** | Background tasks | 1.2.0 |
| **fuzzywuzzy** | Fuzzy matching | 0.18.0 |

### Why Each Package?

- **PyQt6**: Modern, native-looking UI across platforms
- **jobspy**: Scrapes job listings from multiple sites
- **google-auth\***: Secure Gmail authentication
- **schedule**: Simple background task scheduling
- **fuzzywuzzy**: Match emails to jobs intelligently

---

## 🔌 Internet & Connectivity

### Required
- **Internet connection**: For scraping + Gmail
- **Google account**: For Gmail integration (optional)

### Outgoing Ports
- Port 443 (HTTPS): LinkedIn, Indeed, Gmail API
- All outgoing (standard HTTP/HTTPS)

### Firewalls
If behind corporate firewall:
1. Allow access to: `linkedin.com`, `indeed.com`, `gmail.com`
2. Allow Python/PyInstaller executables
3. Allow OAuth2 callback to localhost:8080

---

## 🆘 Troubleshooting Installation

### "Python not found"
```powershell
# Windows: Add Python to PATH
# Control Panel > System > Advanced > Environment Variables
# Add C:\Users\YourName\AppData\Local\Programs\Python\Python311

# Or reinstall Python with "Add to PATH" checked
```

### "pip install" fails
```powershell
# Update pip
python -m pip install --upgrade pip

# Or use Python version directly
python3.11 -m pip install -r requirements.txt
```

### "PyQt6 installation error"
```bash
# Try system-specific installation
pip install PyQt6 --no-binary PyQt6

# Or pre-install Qt libraries (Linux)
sudo apt-get install libqt6core6
```

### "jobspy import error"
```bash
# Ensure latest version
pip install --upgrade jobspy

# Or install from source
pip install git+https://github.com/Bunsly/JobSpy.git
```

### "Permission denied" (macOS/Linux)
```bash
# Fix permissions
chmod +x main.py
chmod +x JobTracker  # if built
sudo chown -R $(whoami) .
```

---

## 🌐 Gmail Setup

### Prerequisites
- Google account (free Gmail account works)
- Access to Google Cloud Console

### Setup Steps

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Click "Create Project"
   - Name it "Job Tracker" or similar
   - Wait for creation

2. **Enable Gmail API**
   - Search for "Gmail API"
   - Click "Gmail API" result
   - Click "Enable"
   - Wait for confirmation

3. **Create OAuth Credentials**
   - Go to "Credentials" (left sidebar)
   - Click "Create Credentials"
   - Choose "OAuth 2.0 Client IDs"
   - Select "Desktop application"
   - Click "Create"
   - Click "Download JSON"

4. **Save Credentials**
   - Save downloaded file as `credentials.json`
   - Place in Job Tracker application folder

5. **Authorize in App**
   - Click "Connect Gmail" in Settings
   - Browser opens Google login
   - Click "Allow" to grant access
   - Done!

---

## 🗂️ File Locations

After first run, your files are at:

### Windows
```
C:\Users\YourUsername\AppData\Local\Programs\JobTracker\
  ├── jobs.db
  ├── config.json
  ├── job_tracker.log
  └── token.json
```

### macOS
```
~/Library/Application Support/JobTracker/
  ├── jobs.db
  ├── config.json
  ├── job_tracker.log
  └── token.json
```

### Linux
```
~/.config/JobTracker/
  ├── jobs.db
  ├── config.json
  ├── job_tracker.log
  └── token.json
```

---

## 🔄 Updating

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Updating Application
1. Download latest `main.py`, `scheduler.py`, etc.
2. Overwrite old files (keep `config.json`, `jobs.db`, `token.json`)
3. Restart application

---

## 🗑️ Uninstalling

### Python Version
```bash
# Simply delete the folder
# Or uninstall libraries
pip uninstall -r requirements.txt -y

# Uninstall Python (if using only for this app)
# Windows: Control Panel > Add/Remove Programs
```

### Executable Version
```
# Simply delete JobTracker.exe
# No registry entries or system files modified
```

### Save Your Data
Before uninstalling, backup:
- `jobs.db` (job database)
- `config.json` (settings)
- Export jobs to CSV from within app

---

## 🔒 Antivirus & Security

### Windows Defender
- PyInstaller .exe may be flagged as "Unknown app"
- This is normal for unsigned executables
- Click "More info" > "Run anyway"

### Third-party Antivirus
- Some antivirus may flag `PyInstaller` executables
- This is because PyInstaller unpacks files at runtime
- Safe to allow - application is open source
- Or compile your own using provided source code

### Safe Practices
1. Only use official distribution channels
2. Verify file checksums if distributed
3. Review source code at: `main.py`, `scheduler.py`, etc.
4. Keep Gmail credentials private

---

## 📊 Performance Tuning

### For Slow Computers
```json
// In config.json
{
  "results_wanted": 25,           // Reduce from 50
  "scrape_interval_hours": 4,     // Increase from 2
  "email_check_interval_minutes": 60  // Increase from 30
}
```

### For Fast Machines
```json
{
  "results_wanted": 100,          // More results
  "scrape_interval_hours": 1,     // More frequent
  "email_check_interval_minutes": 15  // More frequent email checks
}
```

---

## 🐛 Diagnostics

### Enable Debug Logging
Edit `main.py` line 57:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    ...
)
```

### Collect Diagnostics
For support, provide:
1. `job_tracker.log` (last 100 lines)
2. `config.json` (without sensitive data)
3. Python version: `python --version`
4. OS information: `python -c "import platform; print(platform.platform())"`

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Application launches without errors
- [ ] Main window appears with proper size
- [ ] Settings dialog opens and saves
- [ ] Can browse/filter job table
- [ ] "Refresh Jobs Now" works (connects to internet)
- [ ] CSV export creates file
- [ ] Database file created (`jobs.db` appears)
- [ ] Log file created (`job_tracker.log`)

---

## 🎯 Getting Help

### Check These First
1. **README.md** - Feature overview
2. **QUICKSTART.md** - 5-minute setup
3. **job_tracker.log** - Error details
4. This file - Installation help

### Common Resources
- Python: https://www.python.org/
- PyQt6: https://www.riverbankcomputing.com/software/pyqt/
- Gmail API: https://developers.google.com/gmail/api/
- JobSpy: https://github.com/Bunsly/JobSpy

---

**You're all set! Proceed to QUICKSTART.md for first-run setup.**
