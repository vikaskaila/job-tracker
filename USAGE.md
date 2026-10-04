# Job Tracker - Complete Usage Guide

## 📖 Table of Contents
1. [First Launch](#first-launch)
2. [Dashboard Navigation](#dashboard-navigation)
3. [Job Management](#job-management)
4. [Settings Configuration](#settings-configuration)
5. [Gmail Integration](#gmail-integration)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Advanced Tips](#advanced-tips)

---

## 🚀 First Launch

### Initial Startup
When you run `python main.py` or `JobTracker.exe`:

1. **Main window appears** (1200x800 pixels, resizable)
   - Title: "Datta's Job Tracker"
   - Dark mode by default
   - Status bar at bottom shows statistics

2. **Database created** (background)
   - `jobs.db` created if not exists
   - Indexes for performance
   - Empty job list displayed

3. **Configuration loaded**
   - `config.json` created with defaults if missing
   - Search terms: Python Developer, Software Engineer
   - Location: North Rhine-Westphalia, Germany

### First Time Setup

```
┌─────────────────────────────────────────┐
│    Datta's Job Tracker              ▢ ▢ ✕
├─────────────────────────────────────────┤
│ Search: ________________  Status: [All ▼]
├─────────────────────────────────────────┤
│ [Refresh] [Apply] [Export] [Settings] [Gmail]
├─────────────────────────────────────────┤
│ Title | Company | Location | Posted | Status | Link
├─────────────────────────────────────────┤
│                (empty initially)
├─────────────────────────────────────────┤
│ Total: 0 | New: 0 | Applied: 0 | Interview: 0 ...
└─────────────────────────────────────────┘
```

---

## 📊 Dashboard Navigation

### Top Bar Elements

#### Search Box
- **Location**: Left side
- **Function**: Filter jobs in real-time
- **Search fields**: Title, Company, Location
- **Case**: Insensitive
- **Example**: Type "Python" finds "Python Developer" jobs

```
Type here: ________________
↓
Shows only jobs matching search
```

#### Status Filter Dropdown
- **Options**: All, New, Applied, Interview, Rejected, Ghosted, Offer
- **Default**: All
- **Behavior**: Combined with search (search + status)
- **Color codes**:
  - Blue = New
  - Green = Applied
  - Gold = Interview
  - Red = Rejected
  - Gray = Ghosted
  - Bright Green = Offer

### Button Bar

| Button | Function | Keyboard |
|--------|----------|----------|
| **Refresh Jobs Now** | Fetch latest jobs from LinkedIn/Indeed | - |
| **Mark Selected as Applied** | Mark all selected rows as Applied | Ctrl+M |
| **Export to CSV** | Save jobs to Excel file | Ctrl+E |
| **Settings** | Configure app preferences | Ctrl+, |
| **Connect Gmail** | Authenticate with Gmail | - |

---

## 💼 Job Management

### Table Columns

| Column | Sortable | Filterable | Editable |
|--------|----------|-----------|----------|
| **Title** | ✓ | ✓ (search) | ✗ |
| **Company** | ✓ | ✓ (search) | ✗ |
| **Location** | ✓ | ✓ (search) | ✗ |
| **Posted** | ✓ | ✗ | ✗ |
| **Status** | ✓ | ✓ (dropdown) | ✓ (right-click) |
| **Apply Link** | ✗ | ✗ | ✗ |

### Click Actions

#### Double-Click
- **Position**: Apply Link column ("Click to Open")
- **Action**: Opens job URL in default browser
- **Example**: Double-click → Browser opens job page → Apply manually

#### Single Click
- **Selection**: Selects/deselects row
- **Multiple**: Hold Ctrl+Click for multiple selection
- **Bulk actions**: Mark selected, delete selected

#### Right-Click (Context Menu)

```
┌────────────────────────┐
│ Mark as Applied        │
│ Mark as Interview      │
│ Mark as Rejected       │
├────────────────────────┤
│ Add/Edit Note          │
├────────────────────────┤
│ Delete Job             │
└────────────────────────┘
```

### Status Workflow

```
New → Applied → Interview → Offer
                   ↓
                Rejected
```

**Timeline example:**
1. Job scraped → Status = "New"
2. You apply → Status = "Applied" (manual or mark)
3. Interview request email → Status = "Interview" (auto or manual)
4. Got the job! → Status = "Offer" (manual)

---

## ⚙️ Settings Configuration

### Open Settings
Click **Settings** button or press Ctrl+,

```
┌──────────────────────────────────────┐
│         Job Tracker Settings      ✕
├──────────────────────────────────────┤
│
│ Search Terms (one per line):
│ ┌──────────────────────────────────┐
│ │ Python Developer                 │
│ │ Software Engineer                │
│ │ Backend Developer                │
│ │ Full Stack Developer             │
│ └──────────────────────────────────┘
│
│ Location:
│ ┌──────────────────────────────────┐
│ │ North Rhine-Westphalia, Germany  │
│ └──────────────────────────────────┘
│
│ Country:
│ ┌──────────────────────────────────┐
│ │ Germany                          │
│ └──────────────────────────────────┘
│
│ Results per Scrape: [50      ] (10-500)
│ Scrape Interval:    [2   hrs ]
│ Email Check:        [30  min ]
│
│        [Save Settings]  [Cancel]
└──────────────────────────────────────┘
```

### Configuration Options

#### Search Terms
- **What**: Job titles to search for
- **Format**: One per line
- **Examples**:
  ```
  Python Developer
  Senior Developer
  Data Scientist
  Machine Learning Engineer
  ```
- **Impact**: More terms = more jobs found
- **Tip**: More specific = fewer but more relevant jobs

#### Location
- **What**: Geographic area for job search
- **Examples**:
  - "North Rhine-Westphalia, Germany"
  - "Berlin, Germany"
  - "United States"
  - "Remote"
- **Tip**: Specific > Generic

#### Country
- **What**: For Indeed job search
- **Examples**: Germany, USA, UK, Canada
- **Note**: Some sites use location only

#### Results per Scrape
- **Range**: 10 to 500 jobs
- **Default**: 50
- **Impact**: More = slower, but more jobs
- **Note**: LinkedIn/Indeed may limit results

#### Scrape Interval
- **Default**: 2 hours
- **Minimum**: 1 hour
- **Maximum**: 24 hours
- **Tip**: Lower interval with rate limiting to avoid blocks

#### Email Check Interval
- **Default**: 30 minutes
- **Range**: 5 to 1440 minutes (24 hours)
- **Requires**: Gmail connected
- **Tip**: More frequent = quicker status updates

### Save & Apply
1. Make changes
2. Click **Save Settings**
3. Settings saved to `config.json`
4. Scheduler restarts with new config
5. Success dialog appears

---

## 📧 Gmail Integration

### Why Connect Gmail?
- ✅ Auto-detect interview requests
- ✅ Auto-detect rejections
- ✅ Auto-detect offers
- ✅ Auto-update job status
- ✅ Save time vs manual updates

### Setup Steps

#### 1. Get Gmail Credentials
- Go to: https://console.cloud.google.com/
- Create new project
- Enable Gmail API
- Create OAuth 2.0 Desktop Client
- Download JSON file
- Rename to `credentials.json`
- Save to app folder

#### 2. Connect in App
1. Click **Connect Gmail** button
2. Browser opens Google login
3. Sign in with your Gmail account
4. Click **Allow** to grant permissions
5. Browser closes
6. Success message appears
7. Email checking starts automatically

#### 3. What Gets Monitored
- **Unread emails** from last 24 hours
- **Senders**: linkedin.com, indeed.com, company domains
- **Keywords**:
  - Interview: "interview", "scheduled", "call"
  - Rejection: "unfortunately", "we regret", "declined"
  - Offer: "congratulations", "excited to offer"

#### 4. How Matching Works
- Email subject/body compared to job title + company
- Fuzzy matching (tolerates typos)
- Confidence score calculated
- If > 60% match → Status auto-updated
- Email marked as read

**Example:**
```
Email: "We're excited to schedule an interview for Software Engineer"
Job: "Software Engineer at TechCorp"
Confidence: 95% ✓ Match!
Action: Status changed to "Interview"
```

### Troubleshooting Gmail

| Problem | Solution |
|---------|----------|
| Won't connect | Check credentials.json exists |
| Authorization fails | Delete token.json, try again |
| Emails not matching | Ensure company name in email |
| Token expires | App auto-refreshes, ask again if fails |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+M | Mark selected as Applied |
| Ctrl+E | Export to CSV |
| Ctrl+, | Open Settings |
| Ctrl+F | Focus search box |
| Ctrl+Q | Quit application |
| Enter | Open job URL (if selected) |
| Delete | Delete selected job |

---

## 🎯 Advanced Tips

### Search Operators

```
Search: "Berlin"          → Location contains "Berlin"
Search: "Developer"       → Title/Company/Location has "Developer"
Search: "Python Remote"   → Both words must appear
```

### Combining Filters

```
Search: "Python"
Status: "New"
↓
Shows only NEW jobs with "Python" in any field
```

### Bulk Operations

1. Select multiple jobs
   - Click first job
   - Hold Shift+Click last job
   - Or Ctrl+Click each job

2. Perform action
   - Click "Mark Selected as Applied"
   - Or right-click → "Mark as Interview"

3. Result: All selected updated at once

### CSV Export

```
Exported file contains:
- All visible jobs (respects current search/filter)
- Columns: Title, Company, Location, Posted, Status, etc.
- Format: UTF-8 encoded
- Use with: Excel, Google Sheets, Numbers

Example usage:
1. Export to Excel.csv
2. Sort by Status
3. Share with mentors/colleagues
```

### Performance Tips

**If jobs loading slowly:**
- Reduce results per scrape (50 → 25)
- Limit search terms (3 → 1)
- Increase scrape interval (2h → 4h)

**If want more jobs:**
- Increase results per scrape (50 → 100)
- Add more search terms
- Decrease scrape interval (2h → 1h)
- But risks getting blocked by LinkedIn/Indeed

### Notes Feature

1. Right-click any job
2. Select "Add/Edit Note"
3. Add text:
   ```
   Interview scheduled: 2024-03-20 2PM
   Contact: john@company.com
   Salary: €50-60k
   ```
4. Save
5. Notes stored in database
6. Exported to CSV

### Data Management

**Backup your data:**
```bash
# Export jobs to CSV
# In app: Click "Export to CSV"

# Or copy database file
copy jobs.db jobs_backup.db
```

**Delete old jobs:**
```
# Right-click each job → Delete
# Or select multiple → right-click → Delete
```

**Reset everything:**
```
# Delete these files:
- jobs.db (starts fresh)
- config.json (resets to defaults)
- token.json (re-authenticate Gmail)

# Application auto-recreates on next launch
```

---

## 📈 Dashboard Statistics

**Status Bar Shows:**
```
Total: 42 | New: 12 | Applied: 18 | Interview: 8 | 
Rejected: 2 | Offer: 2
```

**What it means:**
- **Total**: All jobs in database
- **New**: Haven't applied yet
- **Applied**: You've applied
- **Interview**: Interview stage
- **Rejected**: Turned down
- **Offer**: Got the job! 🎉

**Use this to:**
- Track progress
- See application rate (Applied / Total)
- Monitor pipeline

---

## 🔄 Automatic Background Tasks

Once running, the app:

**Every 2 hours (default):**
- Fetches new jobs from LinkedIn + Indeed
- Adds to database
- Prevents duplicates
- Updates status bar

**Every 30 minutes (if Gmail connected):**
- Checks unread emails
- Matches to jobs
- Updates status if match found
- Marks email as read

**Respects rate limits:**
- Won't scrape more than once per 30 minutes
- Protects against IP blocking

---

## 🎓 Best Practices

### Daily Usage
```
Morning:
1. Open app
2. Check dashboard (see new jobs)
3. Mark jobs as Applied
4. Notes: interview date/time

Afternoon:
5. Check for emails (auto-updated)
6. Update status if needed

Weekly:
7. Export to CSV
8. Review progress
9. Adjust search terms if needed
```

### Job Application Strategy
```
1. Receive 50 new jobs (auto-scraped)
2. Review 5-10 promising ones
3. Apply to 2-3 per day
4. Mark as Applied when done
5. Wait for responses (monitored via Gmail)
6. Interview preparation when needed
```

### Tracking Success
```
- New job count decreasing? Jobs scraped
- Applied count increasing? You're being active
- Interview count? Good match rate
- Offers coming? Your search criteria working!
```

---

## 🔐 Privacy & Data

**What's stored locally:**
- jobs.db: Job listings, application status
- config.json: Your preferences
- token.json: Gmail access token (encrypted by Google)

**What's NOT stored:**
- Your password
- Full email content
- Browsing history
- Tracking data

**What leaves your computer:**
- Job scraping requests (LinkedIn, Indeed)
- Gmail API calls (with OAuth token)
- Nothing else

---

## 🆘 Common Questions

**Q: Why can't I find any jobs?**
A: Check:
1. Search terms are real job titles
2. Location is correct
3. Internet connection working
4. Check log_file for errors

**Q: Emails not updating status?**
A: Make sure:
1. Gmail is connected
2. Company name in email matches database
3. Email is unread
4. Contains matching keywords

**Q: Getting rate limit warning?**
A: Wait 30 minutes between manual scrapes (protects from blocking)

**Q: How to run without Python installed?**
A: Use the compiled .exe from `build.py`

**Q: Can I edit job details?**
A: Limited support:
- Right-click → Add Note (for extra info)
- Status can be changed
- Delete and re-scrape for updated listings

---

## ✅ You're Ready!

You now understand:
- ✅ Dashboard navigation
- ✅ Job management
- ✅ Settings configuration
- ✅ Gmail integration
- ✅ Best practices

**Next step**: Start using it!

Launch the app and let it find your next great opportunity! 🚀

---

**Questions?** Check **README.md** for comprehensive documentation.
