# Quick Start Guide - Job Tracker v2.0

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (1 minute)

Open PowerShell or Command Prompt in the project folder and run:

```powershell
pip install -r requirements.txt
```

### Step 2: Run the App (30 seconds)

```powershell
python main.py
```

The application window opens immediately showing your job tracker.

✨ **New in v2.0**: Your data is automatically saved to:
- **Windows**: `C:\Users\YourName\AppData\Roaming\DattasJobTracker`
- **Mac/Linux**: `~/.DattasJobTracker`

### Step 3: Configure Search Terms (1 minute)

1. Click **⚙️ Settings** button
2. Enter your desired job titles (one per line):
   - Quality Management
   - Process Improvement  
   - Logistics Quality Intern
3. **Location**: Hamburg, Germany (or your location)
4. **Results per Scrape**: 50 (adjust as needed)
5. Click **"Save Settings"** button

### Step 4: Fetch Your First Jobs (2 minutes)

1. Click **🔄 Refresh Jobs Now** button
2. Wait for scraping to complete (shows in status bar)
3. Jobs appear in the table immediately!

### Step 5: (Optional) Setup Gmail Monitoring

Connect your Gmail to auto-track interview invites, rejections, and offers!

1. Click **⚙️ Settings** button
2. Scroll to **"Gmail Settings (IMAP + App Password)"**
3. Enter your **Gmail email** (e.g., your.email@gmail.com)
4. **Generate an App Password**:
   - Go to [myaccount.google.com/security](https://myaccount.google.com/security)
   - Enable 2-Step Verification (if not already done)
   - Click "App passwords" → Generate for Mail on Windows Computer
   - Copy the 16-character code
5. **Paste the code** in Job Tracker's "App Password" field
6. Click **"Save & Test Connection"** (should show ✓ success)
7. Check **"Enable Gmail Monitoring"** checkbox
8. Click **"Save Settings"**

📧 **Done!** The app will now automatically update job statuses from emails.

**See**: [GMAIL_SETUP.md](GMAIL_SETUP.md) for detailed step-by-step guide

## 📊 Key Features

### 🔍 Search & Filter
- **Search box**: Real-time filter by job title, company, or location
- **Status filter**: Show only New, Applied, Interview, Rejected, Offer, or Ghosted jobs

### 👥 Track Applications
- **Right-click** a job → Change status (Applied, Interview, Rejected, Offer, etc.)
- **Color-coded statuses**:
  - 🔵 New (Blue)
  - 🟢 Applied (Green)
  - 🟠 Interview (Orange)
  - 🔴 Rejected (Red)
  - 💚 Offer (Dark Green)
  - ⚫ Ghosted (Gray)

### 🎯 Apply Directly
- **Double-click** "Open Link" column → Opens job posting in browser
- **Right-click** row → "Open Apply Link" option

### 📧 Auto-Update from Gmail
- App checks your email every 30 minutes (adjustable)
- Automatically detects:
  - ✅ Interview invitations → Updates to "Interview"
  - ❌ Rejections → Updates to "Rejected"
  - 🎉 Offers → Updates to "Offer"
- Shows notification when jobs are updated

### 📊 Export & Backup
- Click **"📊 Export to CSV"** to save all jobs to spreadsheet
- All data automatically backed up locally (never in cloud)

### 🌙 Theme Switcher
- **Themes** menu → Select Light, Dark, or Pastel theme
- Theme preference saved automatically
- Light: Bright white interface
- Dark: Easy on the eyes (default)
- Pastel: Soft, colorful design

## ⚙️ Default Configuration

The app starts with these settings:

| Setting | Value | Adjustable |
|---------|-------|-----------|
| Search Terms | Quality Management, Process Improvement, etc. | Yes ✓ |
| Location | Hamburg, Germany | Yes ✓ |
| Results per Scrape | 50 jobs | Yes ✓ |
| Auto-scrape Interval | 2 hours | Yes ✓ |
| Email Check Interval | 30 minutes | Yes ✓ |
| Theme | Dark | Yes ✓ |

Change any settings anytime in **⚙️ Settings** → **Save Settings**

## 💡 Pro Tips

### Accelerate Job Scraping
- Increase "Results per Scrape" (up to 500)
- Reduce scrape interval to 1 hour instead of 2
- Use more specific search terms

### Get Better Email Matches
- Make sure company name in database **exactly matches** email sender
- Use common abbreviations Gmail uses (e.g., "ACME Corp" → "ACME Corporation")
- Job title should appear in email subject line

### Keep Data Organized
- Regularly mark jobs as Applied/Rejected to keep list clean
- Add notes for interviews (right-click → custom notes)
- Export to CSV monthly for backup

### Performance
- Limit search terms to 5-7 for faster scraping
- Set scrape interval to 2-4 hours (more frequent = slower app)
- Close other programs if scraping takes too long

## 🛠️ Troubleshooting

### No jobs appearing?
1. Check your internet connection
2. Verify search terms aren't too specific
3. Try different location (e.g., "Germany" instead of "Hamburg")
4. Wait 2+ minutes for scraping to complete
5. Check **Status bar** at bottom for messages

### Gmail not connecting?
1. See [GMAIL_SETUP.md](GMAIL_SETUP.md) for detailed setup
2. Verify you're using **App Password** (not main Gmail password)
3. Verify **IMAP is enabled** in Gmail settings
4. Verify **2-Step Verification is enabled**
5. Try clicking "Save & Test Connection" again

### Jobs not updating from emails?
1. Verify **"Enable Gmail Monitoring"** is checked
2. Make sure company name matches database
3. Wait for next email check (every 30 min by default)
4. Check app log: `%APPDATA%\DattasJobTracker\app.log`

### Forgot where data is stored?
- **Windows**: `C:\Users\YourName\AppData\Roaming\DattasJobTracker`
- **Mac**: `~/.DattasJobTracker`
- **Linux**: `~/.DattasJobTracker`

### Want to move the app?
- You can move `main.py` anywhere!
- Your data stays in the above locations automatically
- The `.exe` file (when you build it) also relocates data correctly

## 📚 More Help

- **Menu** → **Help** → Shows in-app guides
- **Menu** → **Themes** → Switch themes
- **Menu** → **File** → Exit app
- **Right-click** any job → Access all job actions
- Hover over fields for more info

## 🎬 First Time Workflow

```
1. Settings → Set search terms → Save
   ↓
2. Refresh Jobs Now → Wait for scraping
   ↓
3. Jobs appear in table
   ↓
4. Click job → Right-click → "Open Apply Link"
   ↓
5. Fill application, submit
   ↓
6. Back to app → Right-click job → Mark as "Applied"
   ↓
7. Gmail monitoring auto-updates when responses come in ✨
   ↓
8. Repeat for each job!
```

## 📞 Questions?

- See [README.md](README.md) for comprehensive documentation
- See [GMAIL_SETUP.md](GMAIL_SETUP.md) for email setup details
- Check **Help menu** inside the app for quick guides
- Check app logs at: `%APPDATA%\DattasJobTracker\app.log`

---

**🎯 You're all set! Ready to track your job applications? Start by clicking "🔄 Refresh Jobs Now"!**
