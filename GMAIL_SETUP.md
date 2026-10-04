# Gmail Integration Setup Guide

## Overview
Job Tracker v2.0 now uses **IMAP + App Password** instead of OAuth2. This is simpler, more reliable, and doesn't require creating a Google Cloud project!

The app automatically monitors your Gmail inbox for job application responses (interviews, offers, rejections) and updates your job status accordingly.

## Quick Setup (5 minutes)

### Step 1: Enable IMAP in Gmail Settings

1. Go to **Gmail.com** → Click gear icon (Settings)
2. Click **"See all settings"**
3. Go to **"Forwarding and POP/IMAP"** tab
4. Select **"Enable IMAP"**
5. Click **"Save Changes"** at the bottom

### Step 2: Enable 2-Step Verification (if not already enabled)

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **"Security"** in the left sidebar
3. Find **"2-Step Verification"**
4. Click it and follow the setup steps (usually text/call confirmation)
5. Once enabled, proceed to Step 3

### Step 3: Generate App Password

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **"Security"** in the sidebar
3. Scroll down and find **"App passwords"** (only appears AFTER 2-Step is enabled)
4. Select: 
   - **App**: Mail
   - **Device**: Windows Computer (or your OS)
5. Click **"Generate"**
6. Google will show a **16-character code** like: `xxxx xxxx xxxx xxxx`
7. **Copy this code** (you'll need it in the next step)

### Step 4: Add to Job Tracker

1. **Open Job Tracker** on your computer
2. Click **⚙️ Settings** button
3. Scroll down to **"Gmail Settings (IMAP + App Password)"** section
4. **Gmail Email**: Paste your Gmail address (e.g., `your.email@gmail.com`)
5. **App Password**: Paste the 16-char code (no spaces)
6. Click **"Save & Test Connection"** button
7. If successful: ✓ Confirmation message appears
8. Check **"Enable Gmail Monitoring"** checkbox
9. Click **"Save Settings"** button

**Done!** At this point, Job Tracker will automatically:
- Check your email every 30 minutes (adjustable in Settings)
- Detect job-related keywords
- Automatically update job statuses

## What Job Keywords Does It Detect?

The app scans email subject and body for these keywords:

### ✅ Interview Keywords
- `interview`, `meeting`, `call`, `gespräch`, `termin`, `vorstellungsgespräch`, `gesprächstermin`
- **Auto-updates status to**: Interview

### ❌ Rejection Keywords  
- `unfortunately`, `not proceeding`, `nicht in Betracht`, `ablehnung`, `absage`, `leider nicht`, `we decided`, `regret`
- **Auto-updates status to**: Rejected

### 🎉 Offer Keywords
- `offer`, `position`, `angebot`, `stelle`, `job offer`, `welcome`, `willkommen`, `können wir dir anbieten`
- **Auto-updates status to**: Offer

The app uses **fuzzy matching** to connect emails to jobs in your database:
- Matches company name in email to company in database
- Matches job title in email subject line
- Only updates if confidence score ≥ 50%

## How to Customize Email Check Frequency

In **Settings → Email Check Interval**:
- `5` = Check every 5 minutes
- `30` = Check every 30 minutes (default)
- `60` = Check every hour
- `120` = Check every 2 hours

## Troubleshooting

### ❌ "Connection Failed" Error

**Issue**: Password or IMAP setting is wrong

**Solutions**:
1. Verify you're using the **16-character app password** (not your main Gmail password)
2. Verify IMAP is **enabled** in Gmail Settings → Forwarding and POP/IMAP
3. Verify 2-Step Verification is **enabled** (required for app passwords)
4. Try copying the password again and re-pasting (sometimes copy issues)

### ❌ "App passwords" Option Not Showing

**Issue**: 2-Step Verification not enabled

**Solution**:
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Find and enable **"2-Step Verification"**
3. Complete the verification process
4. Then the "App passwords" option will appear

### ❌ Jobs Not Updating from Emails

**Issue**: Emails aren't matching to jobs correctly

**Solutions**:
1. Check that **"Enable Gmail Monitoring"** is **checked** in Settings
2. Verify company name in email matches company name in job database (fuzzy matching requires ~50% match)
3. Check the job title appears in email subject line or body
4. Wait for the next email check (runs every 30 min by default)
5. Check app.log file for errors: 
   - Windows: `C:\Users\YourUsername\AppData\Roaming\DattasJobTracker\app.log`

### ❌ Email Check Stopped Working

**Issue**: Thread crashed or Gmail password expired

**Solutions**:
1. Check Excel: Did email password change recently?
2. If password changed: Update in Settings, test connection, save
3. Check app logs at: `%APPDATA%\DattasJobTracker\app.log`
4. Restart the app

### ✅ Want to Disable Gmail Monitoring?

Simply **uncheck** "Enable Gmail Monitoring" in Settings and save. The app will stop checking emails.

## Security & Privacy Notes

🔒 **What does the app do with your email?**
- ✅ Read email subjects and bodies
- ✅ Mark matched emails as "read"
- ✅ Extract company/job info from emails
- ❌ The app **does NOT**:
  - Delete emails
  - Send emails
  - Store passwords (kept in config.json locally only)
  - Share anything with third parties

🔐 **Best Practices**:
1. Use this only with your job application Gmail account
2. The app password is specific to "Job Tracker" - you can revoke it anytime
3. Your actual Gmail password is never used or stored
4. All data is stored locally on your computer

## If You Want Maximum Privacy

Create a dedicated Gmail account just for job applications:
1. Create new Gmail account (e.g., `jobs.tracking.2026@gmail.com`)
2. Forward job emails there from your main account (using Gmail filters)
3. Use that account's app password in Job Tracker
4. Enjoy full monitoring without touching your main email

---

## Questions?

Refer to [QUICKSTART.md](QUICKSTART.md) or [README.md](README.md) for other app features.
