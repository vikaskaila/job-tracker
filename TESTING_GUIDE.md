# Testing Guide - Optimization & Fixes

## Quick Verification Checklist

### ✅ Pre-Testing
- [ ] Python syntax verified
- [ ] New dependencies installed (langdetect, google-cloud-translate)
- [ ] Virtual environment activated
- [ ] Groq API key configured in settings
- [ ] LaTeX tools installed (MiKTeX/MacTeX/texlive)

---

## Test 1: Job Scraping (Fixed: 7 → 50+ jobs)

### Setup
1. Launch the Job Tracker application
2. Go to Settings
3. Set "Results per Scrape" to **50**
4. Set "Search Terms" to: `Python Developer`
5. Set "Location" to: `Germany` (or your preferred location)

### Execute
1. Click "🔄 Refresh Jobs Now"
2. Monitor the status bar - should show scraping in progress
3. Wait for completion (~30-60 seconds depending on internet)

### Verify
**Expected Results**:
- [ ] Total jobs added: **50+ (not just 7)**
- [ ] Mix of Indeed and LinkedIn jobs visible in table
- [ ] Status bar shows: "✓ 50 new jobs added"
- [ ] Logs contain: "Added 50 new jobs from Python Developer"

**Check Database**:
```bash
# From PowerShell in venv directory
python -c "
import sqlite3
conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*), site FROM jobs GROUP BY site')
for count, site in cursor.fetchall():
    print(f'{site}: {count} jobs')
cursor.execute('SELECT COUNT(*) FROM jobs')
print(f'Total: {cursor.fetchone()[0]} jobs')
conn.close()
"
```

**Expected Output**:
```
linkedin: 25+ jobs
indeed: 25+ jobs
Total: 50+ jobs
```

❌ **If Failing**:
- Check logs for errors: `more $PROFILE/../JobTracker/app.log`
- Verify internet connection
- Check JobSpy library version

---

## Test 2: Language Detection & Translation

### Setup
1. Ensure German job description is in database
2. Or manually add a German job posting for testing

### Execute
```bash
# Test language detection
python -c "
from main import detect_language

# Test cases
tests = [
    ('Dies ist ein deutscher Text', 'de'),  # German
    ('C'est du texte français', 'fr'),      # French
    ('This is English text', 'en'),         # English
]

for text, expected in tests:
    result = detect_language(text)
    status = '✓' if result == expected else '✗'
    print(f'{status} {text[:30]}... → {result} (expected {expected})')
"
```

**Expected Output**:
```
✓ Dies ist ein deutscher Text... → de (expected de)
✓ C'est du texte français... → fr (expected fr)
✓ This is English text... → en (expected en)
```

### Execute Translation Test
```bash
# Test translation (requires Groq API key)
python -c "
from main import translate_text
import os

groq_key = os.getenv('GROQ_API_KEY')  # or hardcode for testing

german_text = 'Suche einen Senior Python Developer mit 5 Jahren Erfahrung in Django.'
translated = translate_text(german_text, 'de', 'en', groq_key)
print(f'German: {german_text}')
print(f'English: {translated}')
"
```

**Expected Output**:
```
German: Suche einen Senior Python Developer mit 5 Jahren Erfahrung in Django.
English: [English translation of above]
```

### Verify in Resume Generation
1. Create tailored resume for a job with German description
2. Check application logs for:
   - [ ] "Analyzing job description language..."
   - [ ] "Detected job description language: de"
   - [ ] "Translating job description from de to English..."
   - [ ] "Translation complete"

❌ **If Language Detection Fails**:
- Wrong language detected?
  - Increase text to 20+ characters for testing
  - Use clearer language samples
- Missing langdetect?
  - Reinstall: `pip install langdetect`

❌ **If Translation Fails**:
- Check Groq API key is set
- Check internet connection
- Verify Groq API has enough free credits

---

## Test 3: LaTeX Compilation & Validation

### Setup
1. Delete `resume_*.pdf` files from generated folder (to force regeneration)
2. Have a German job description in database

### Execute Resume Generation
1. Click on a job in the table
2. Click "Generate Resume"
3. Monitor:
   - [ ] See "Generating tailored resume..."
   - [ ] Check application logs

### Verify LaTeX Validation
Check logs for:
```
Validating LaTeX content...
LaTeX validation complete
```

### Verify Compilation
Check logs for:
```
Attempting LaTeX compilation with xlatex...
✅ xlatex compilation successful
✅ Successfully generated PDF: C:\...\resume_*.pdf
```

OR (if xlatex not installed):
```
Attempting LaTeX compilation with pdflatex...
✅ pdflatex compilation successful
✅ Successfully generated PDF: C:\...\resume_*.pdf
```

### Verify PDF Created
```powershell
# Check if PDFs were created
Get-ChildItem C:\Users\$env:USERNAME\AppData\Roaming\JobTracker\generated\*.pdf -ErrorAction SilentlyContinue | Select-Object Name, Length
```

Expected output: List of PDF files with sizes > 50KB

**Verify PDF Readable**:
1. Open generated PDF in Adobe Reader or browser
2. Check that resume content is present
3. Verify formatting looks correct

❌ **If LaTeX Compilation Fails**:

**Error: "LaTeX tools not found"**
- [ ] Install LaTeX tools (see LATEX_INSTALLATION_GUIDE.md)
- [ ] Restart computer after installation
- [ ] Verify PATH: `Get-Command pdflatex`

**Error: "LaTeX compilation failed with xlatex"**
- [ ] Try pdflatex only (xlatex is optional)
- [ ] Check logs for specific errors
- [ ] Validate UTF-8 encoding

**Error: "Brace balance warning"**
- [ ] This is a warning, not fatal
- [ ] Check if PDF was still generated
- [ ] May need to adjust LaTeX generation prompt

**Error: "PDF not generated"**
- [ ] Check temp directory exists
- [ ] Check disk space available
- [ ] Check permissions on GENERATED_DIR
- [ ] Try a simpler resume template

---

## Test 4: Resume Generation with Optimized Prompt

### Setup
1. Have multiple job postings in database
2. At least one in German (for language test)
3. At least one in English (baseline)

### Execute
1. English Job: Generate resume
   - Monitor logs for prompt success
   - Verify PDF creation
   
2. German Job: Generate resume
   - Monitor logs for language detection
   - Monitor logs for translation
   - Verify PDF creation
   - Compare quality vs English

### Verify Prompt Quality
Check logs for new messages:
```
Generated tailored LaTeX resume (match score: 75.5%)
```

**Expected Output**:
- Match score: 70-90% (good tailoring)
- No markdown code blocks in LaTeX
- Valid LaTeX structure
- PDF compiles successfully

### Compare Output
1. Open both PDFs
2. Check:
   - [ ] German job resume translated correctly
   - [ ] Keywords from job description visible in resume
   - [ ] Formatting is professional
   - [ ] Sections are properly organized
   - [ ] No truncation or missing content

❌ **If Quality is Poor**:
- Check prompt in logs
- Verify Groq API is responsive
- Compare with baseline English job
- Check generated LaTeX structure

---

## Test 5: Complete Workflow (End-to-End)

### Scenario: Scrape, Detect Language, Tailor, Generate Resume

**Execute**:
1. Start app
2. Go to Settings
3. Add search terms: `"Manager"`, `"Analyst"`
4. Set results: 50
5. Click "Refresh Jobs Now"
6. Wait for completion
7. Sort by date (newest first)
8. For first 3 jobs:
   - Click on job
   - Click "Generate Resume"
   - Monitor logs
   - Verify PDF created

### Verify Each Step
- [ ] Scraping completed (50+ jobs)
- [ ] Jobs from LinkedIn and Indeed mixed
- [ ] Language detection worked (check logs)
- [ ] Translation worked (if German, check logs)
- [ ] LaTeX generated successfully
- [ ] PDF compiled without errors
- [ ] Resume shows tailored content

### Monitor
**Check app.log** for these success markers:
```
✓ Scraping for: Manager
✓ Added 50+ new jobs
✓ Detecting job language
✓ Generating tailored LaTeX resume (match score: 75%)
✓ LaTeX compilation successful
✓ Successfully generated PDF
```

---

## Performance Benchmarks

Use these as reference:

| Operation | Expected Time | Status |
|-----------|----------------|--------|
| Job scraping (50 jobs) | 30-60 sec | Pass/Fail |
| Language detection | <100 ms | Pass/Fail |
| Translation (German) | 3-5 sec | Pass/Fail |
| LaTeX generation | 2-3 sec | Pass/Fail |
| PDF compilation | 5-10 sec | Pass/Fail |
| **Total (1 job)** | ~15-25 sec | Pass/Fail |

**If Slower**:
- Check internet speed
- Monitor CPU/RAM usage
- Check Groq API response times

---

## Log File Analysis

### Location
```
C:\Users\{USERNAME}\AppData\Roaming\JobTracker\app.log
```

### Search for Key Messages
```bash
# Last 50 lines of log
tail -n 50 app.log

# Find all errors
Select-String "ERROR" app.log | tail -n 20

# Find language detection
Select-String "language" app.log -CaseSensitive $false

# Find LaTeX compilation
Select-String "compilation|LaTeX" app.log | tail -n 20
```

### expected Messages (Copy into log to verify)
```
✓ Language detection worked: "Detected job description language: de"
✓ Translation worked: "Translating job description from de to English..."
✓ Validation worked: "LaTeX validation complete"
✓ Compilation worked: "xlatex compilation successful" OR "pdflatex compilation successful"
✓ Generation complete: "Successfully generated PDF"
```

---

## Troubleshooting Decision Tree

```
Problem: Only 7 jobs scraped
├─ Check if idx > 6 line was removed
├─ Check requirements.wanted setting (should be 50+)
└─ Check logs for early break

Problem: Only LinkedIn jobs (no Indeed)
├─ Check JobSpy site_name parameter: ["linkedin", "indeed"]
├─ Verify Indeed jobs returned by JobSpy
└─ Check database has mix

Problem: German not detected
├─ Text too short? (needs 10+ chars)
├─ Check langdetect installed
├─ Verify language is German (not similar)
└─ Use explicit language tests

Problem: Translation failed
├─ Groq API key set?
├─ Check internet connection
├─ Check Groq free tier limit
└─ Check logs for API errors

Problem: LaTeX compilation failed
├─ LaTeX tools installed?
├─ PATH environment variable set?
├─ Restarted computer after install?
├─ Disk space available?
└─ Check LaTeX syntax in logs

Problem: Poor resume quality
├─ Check prompt wording in code
├─ Verify Groq response quality
├─ Check LaTeX syntax validation
├─ Compare heat.score in logs
└─ Check job description language
```

---

## Validation Checklist Before Using

- [ ] All syntax tests passed
- [ ] Dependencies installed (langdetect, google-cloud-translate)
- [ ] Job scraping returns 50+ jobs
- [ ] Language detection works for German
- [ ] Translation produces readable English
- [ ] LaTeX compilation succeeds (if tools installed)
- [ ] PDF files created in generated folder
- [ ] Resume content appears in PDFs
- [ ] Logs show no unexpected errors
- [ ] No critical errors in 1000+ job processing

---

## Success Criteria

✅ **All Tests Passing**: System is ready for production use  
⚠️ **Some Tests Failing**: See troubleshooting section above  
❌ **Critical Tests Failing**: Check prerequisites section  

**Ready When**:
- [ ] 50+ jobs per scrape
- [ ] Mix of Indeed/LinkedIn
- [ ] German jobs translated
- [ ] Resumes generated with PDFs
- [ ] No critical errors in logs

---

Enjoy your optimized and fixed Job Tracker! 🎯
