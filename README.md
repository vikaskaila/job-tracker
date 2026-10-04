# Personal Job Tracker - Desktop Application

A single executable desktop app for Windows/Mac/Linux that automatically fetches job listings from LinkedIn and Indeed, tracks applications, and monitors Gmail for responses.

## Features

✅ **Job Scraping**
- Automatically fetches jobs from LinkedIn and Indeed every 2 hours
- Configurable search terms and location
- Prevents duplicate job entries
- Rate limiting to avoid being blocked

✅ **Application Tracking**
- Track application status: New, Applied, Interview, Rejected, Ghosted, Offer
- Add custom notes to jobs
- Mark jobs with custom status
- Export jobs to CSV

✅ **Gmail Integration**
- OAuth2 authentication with Gmail
- Automatically detect rejections, interview invites, and offers
- Fuzzy matching to link emails to job entries
- Auto-update job status from emails

✅ **User Interface**
- Modern dark mode design
- Clean table view with sorting and filtering
- System tray integration
- Desktop notifications

✅ **Desktop Notifications**
- Alert when status changes to Interview/Offer
- System tray icon for quick access

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
cd f:\newJobScrappingTool
pip install -r requirements.txt
```

### Step 2: Gmail Setup (Optional but Recommended)

To enable Gmail integration:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API
4. Create an OAuth 2.0 Client ID (Desktop application)
5. Download the credentials as `credentials.json`
6. Place `credentials.json` in the app directory

When you first click "Connect Gmail" in the app, it will open a browser to authenticate.

### Step 3: Run the Application

```bash
python main.py
```

## Usage

### Dashboard
- **Search**: Filter jobs by title, company, or location
- **Status Filter**: Show only jobs with specific status
- **Refresh Jobs Now**: Manually trigger job scraping
- **Mark Selected as Applied**: Bulk-mark selected jobs as applied
- **Export to CSV**: Export all jobs to a CSV file

### Settings
- **Search Terms**: Comma-separated job titles to search for
- **Location**: Job search location
- **Country**: Country for Indeed jobs
- **Results per Scrape**: Number of jobs to fetch per scrape
- **Scrape Interval**: Hours between automatic scrapes (default: 2)
- **Email Check Interval**: Minutes between email checks (default: 30)

### Right-Click Menu
- **Mark as Applied**: Mark job as applied
- **Mark as Interview**: Mark job as interview stage
- **Mark as Rejected**: Mark job as rejected
- **Add/Edit Note**: Add custom notes to a job
- **Delete Job**: Remove job from tracker

### Double-Click Apply Link
Double-click the "Click to Open" link in any job row to open the job URL in your default browser.

## Configuration

Settings are saved to `config.json`:

```json
{
    "search_terms": ["Python Developer", "Software Engineer"],
    "location": "North Rhine-Westphalia, Germany",
    "country": "Germany",
    "results_wanted": 50,
    "scrape_interval_hours": 2,
    "email_check_interval_minutes": 30,
    "gmail_connected": false
}
```

## Database

Jobs are stored in `jobs.db` (SQLite database) with the following fields:

- **id**: Unique identifier
- **title**: Job title
- **company**: Company name
- **location**: Job location
- **posted_date**: Date posted
- **description_snippet**: Job description (truncated)
- **apply_link**: URL to apply
- **applied_date**: When you applied
- **status**: Job status (New, Applied, Interview, Rejected, Ghosted, Offer)
- **last_email_matched**: Last email that matched this job
- **notes**: Custom notes

## Error Handling

The application includes robust error handling for:

- **LinkedIn/Indeed Blocking**: Shows warning and suggests waiting
- **Gmail Token Expiration**: Automatically attempts refresh, shows re-authenticate button
- **Network Issues**: Graceful offline mode
- **Duplicate Jobs**: Deduplicates by apply link

## Logs

Application logs are saved to `job_tracker.log`. Check this file if you encounter issues.

## Building as Executable

### Windows (.exe)

```bash
# Install PyInstaller
pip install pyinstaller

# Build single executable
pyinstaller --name "JobTracker" ^
            --onefile ^
            --windowed ^
            --icon=path/to/icon.ico ^
            --add-data "credentials.json:." ^
            --hidden-import=jobspy ^
            --hidden-import=schedule ^
            --hidden-import=googleapiclient ^
            --hidden-import=google_auth_oauthlib ^
            main.py
```

The executable will be in the `dist/` folder.

### Mac

```bash
pyinstaller --name "JobTracker" \
            --onefile \
            --windowed \
            --hidden-import=jobspy \
            --hidden-import=schedule \
            --hidden-import=googleapiclient \
            --hidden-import=google_auth_oauthlib \
            main.py
```

### Linux

```bash
pyinstaller --name JobTracker \
            --onefile \
            --windowed \
            --hidden-import=jobspy \
            --hidden-import=schedule \
            --hidden-import=googleapiclient \
            --hidden-import=google_auth_oauthlib \
            main.py
```

## Project Structure

```
newJobScrappingTool/
├── main.py                 # Main application
├── scheduler.py            # Background scheduler
├── gmail_manager.py        # Gmail integration
├── utils.py               # Utilities (tray, notifications, styling)
├── requirements.txt       # Python dependencies
├── config.json           # User configuration (auto-created)
├── jobs.db              # SQLite database (auto-created)
├── credentials.json     # Gmail credentials (optional)
├── token.json          # Gmail token (auto-created after auth)
└── job_tracker.log     # Application logs
```

## Troubleshooting

### "JobSpy not installed"
```bash
pip install jobspy
```

### Gmail authentication not working
1. Ensure `credentials.json` is in the app directory
2. Check Google Cloud Console for correct OAuth setup
3. Try deleting `token.json` and re-authenticating

### Jobs not scraping
1. Check `job_tracker.log` for error messages
2. Verify search terms are correct
3. Check internet connection
4. Wait 30 minutes before trying again (rate limiting)

### No emails being detected
1. Verify Gmail is connected in Settings
2. Check that you have unread emails in Gmail
3. Ensure email contains job title or company name
4. Check `job_tracker.log` for matching score details

## Performance Tips

1. **Adjust scrape interval**: Lower interval = more jobs but higher chance of blocking
2. **Use specific search terms**: More targeted searches reduce false matches
3. **Enable Gmail**: Auto-update status saves manual work
4. **Export regularly**: Backup your job list periodically

## Privacy & Security

- All data is stored locally on your computer
- No credentials sent to external servers except Gmail OAuth (official Google API)
- SQLite database is unencrypted (use system encryption for security)
- Email tokens refreshed automatically

## Known Limitations

- LinkedIn may block IP after multiple scrapes (rate limiting helps)
- Indeed has stricter rate limiting (2 hour minimum between scrapes recommended)
- Gmail matching works best with descriptive company names in emails
- Very long job descriptions truncated to 500 characters in database

## Future Enhancements

- [ ] Desktop notifications (Windows notifications library)
- [ ] Application history timeline
- [ ] Interview scheduler
- [ ] Resume upload and version control
- [ ] Salary tracking
- [ ] Contact notes
- [ ] Dark mode toggle
- [ ] Custom status categories
- [ ] Multiple search profiles

## License

This is a personal project. Feel free to modify for your own use.

## Support

For issues or feature requests, check:
1. `job_tracker.log` for error details
2. This README for common troubleshooting steps

---

**Built with Python + PyQt6 + JobSpy + Gmail API**
