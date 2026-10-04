# LaTeX Resume Tailoring Workflow

## Overview

This document describes the new **LaTeX-based resume tailoring workflow** that has been implemented in the Job Tracker application. This workflow uses Groq AI to intelligently tailor your resume and cover letter for specific job postings.

## Key Features

### 1. **Smart Job Description Fetching**
- For LinkedIn jobs and other web postings, the system automatically fetches full job descriptions from URLs
- Fallback to basic job info if web scraping fails
- Supports Indeed, LinkedIn, and other job board formats

### 2. **LaTeX Resume Processing**
- Reads your base LaTeX resume template (.tex file)
- Uses Groq AI to intelligently tailor the LaTeX content
- Preserves LaTeX structure and formatting
- Stores tailored LaTeX as `.tex` file for portability

### 3. **Cover Letter Generation**
- Extracts base cover letter from DOCX (.docx) file
- Tailors cover letter using Groq AI for specific job
- Stores as plain text file for easy editing
- Returns in business letter format

### 4. **PDF Generation On-Demand**
- LaTeX is compiled to PDF only when user clicks to view
- Reduces processing time and storage requirements
- Handles LaTeX compilation failures gracefully
- Allows fallback to viewing raw LaTeX file if compilation fails

### 5. **Match Scoring**
- Resume match score: TF-IDF similarity between job description and tailored resume
- Cover letter match score: TF-IDF similarity between job description and tailored cover letter
- Displayed in success dialog and database for tracking

## Workflow Architecture

```
User clicks "Generate Tailored Documents"
           ↓
Check Groq API key & base documents
           ↓
Fetch job description (if empty)
    ├─ Try web scraping from job URL
    ├─ LinkedIn, Indeed, general job boards
    └─ Fallback to basic job title + company
           ↓
Read base LaTeX resume template
           ↓
Call Groq AI → Tailor LaTeX for job
    ├─ Sends job title, company, description
    ├─ Sends base LaTeX template
    └─ Returns tailored LaTeX
           ↓
Read base cover letter (DOCX)
           ↓
Call Groq AI → Tailor cover letter
    ├─ Sends job requirements
    ├─ Sends base cover letter text
    └─ Returns tailored cover letter (business letter format)
           ↓
Calculate match scores (TF-IDF similarity)
           ↓
Save files to GENERATED_DIR
    ├─ {job_id}_resume.tex (tailored LaTeX)
    └─ {job_id}_cover.txt (tailored cover letter)
           ↓
Mark in database with file paths & match scores
           ↓
Show success dialog with match scores
           ↓
User sees ✓ checkmarks in table for Resume & Cover columns
           ↓
User DOUBLE-CLICKS Resume icon (column 10)
           ↓
On-demand LaTeX→PDF compilation
    ├─ Reads .tex file
    ├─ Compiles using xlatex or pdflatex
    ├─ Generates {job_id}_resume.pdf
    └─ Opens PDF viewer
           ↓
User sees compiled resume
```

## File Storage

Generated documents are stored in: `%APPDATA%\JobTracker\generated\` (on Windows)

### File Structure
```
JobTracker/generated/
├── job_12345_resume.tex          (LaTeX source - ~10-15KB)
├── job_12345_resume.pdf          (Generated only on demand - ~50-200KB)
├── job_12345_cover.txt           (Plain text cover letter - ~5-10KB)
├── job_67890_resume.tex
├── job_67890_resume.pdf
└── job_67890_cover.txt
```

### Why This Architecture?

1. **LaTeX `.tex` files are text** - small, portable, version-control friendly
2. **PDFs generated on-demand** - only created when user wants to view
3. **Reduces disk usage** - no need to store large PDFs for jobs not viewed
4. **Supports offline** - can regenerate PDFs if LaTeX tools are installed later
5. **Easy editing** - .tex files can be manually edited with any text editor

## Setup Requirements

### 1. **Groq API Key**
- Visit [Groq Console](https://console.groq.com)
- Create API key
- Add to Settings → Resume & Cover Letter Generation

### 2. **Base Documents**
In Settings → Resume & Cover Letter Generation:
- **Base Resume**: Path to your LaTeX template (`.txt` or `.tex`)
  - Should contain LaTeX code with sections for skills, experience, education
  - Use `\section{}`, `\subsection{}` formatting
  
- **Base Cover Letter**: Path to your Word document (`.docx`)
  - Should contain your generic cover letter
  - Will be extracted as plain text and tailored

### 3. **Optional: LaTeX Installation** (for PDF compilation)
For full PDF generation on-demand, install:
- **Windows**: 
  - [MiKTeX](https://miktex.org/) - Comprehensive LaTeX distribution
  - [TeX Live](https://www.tug.org/texlive/) - Alternative (cross-platform)
  
- After installation, `pdflatex` or `xlatex` commands should work

**Note**: If LaTeX is not installed, you can:
- Still tailor documents successfully
- View the `.tex` files with any text editor
- Install LaTeX later and the PDFs will be generated on-demand

### 4. **Python Dependencies**
All required packages are in `requirements.txt`:
```
requests           - Web scraping job descriptions
beautifulsoup4     - HTML parsing
python-docx        - DOCX file extraction
groq               - AI API
scikit-learn       - Match scoring
```

Install with: `pip install -r requirements.txt`

## Usage

### Step 1: Configure Settings
1. Open app → Click ⚙️ Settings
2. Fill in:
   - Groq API Key
   - Path to base LaTeX resume
   - Path to base cover letter DOCX
3. Click Save

### Step 2: Scrape Jobs
1. Click 🔄 Refresh Jobs Now
2. Or configure email monitoring for automatic scraping
3. Jobs appear in table

### Step 3: Generate Tailored Documents
**Method 1: Via Generate Button (if available)**
- Select job row
- Click "Generate Tailored Documents" button
- Follow progress dialog

**Method 2: Via Settings Tab**
- In SETTINGS tab (if available)
- Find "Generate Tailored Documents" button
- Select job from dropdown
- Click Generate

**Method 3: Via Context Menu (if available)**
- Right-click on job row
- Select "Generate Tailored Documents"
- Confirm

### Step 4: View Results
1. Look for ✓ checkmarks in "Resume" and "Cover" columns
   - ✓ = Generated (green)
   - ✗ = Not generated (gray)

2. Double-click Resume icon (✓ checkmark) to:
   - Compile LaTeX to PDF (if LaTeX installed)
   - View compiled PDF in your default viewer
   - Or open .tex file if LaTeX not available

3. Double-click Cover icon to:
   - Open cover letter text file in default text editor

### Step 5: Edit & Submit
1. **Review generated documents** before applying
2. **Edit if needed**:
   - .tex file: Edit with any text editor, recompile
   - .txt file: Edit with any text editor
3. **Download/export** for job application

## Quality Indicators

### Match Scores
- **80-100%**: Excellent relevance to job
- **60-80%**: Good relevance, minor adjustments suggested
- **40-60%**: Moderate relevance, consider editing
- **0-40%**: Low relevance, major edits recommended

### Database Tracking
In table and database:
- `generated_resume_path`: File path to `.tex` file
- `generated_cover_path`: File path to `.txt` file
- `match_score_resume`: Resume similarity percentage
- `match_score_cover`: Cover letter similarity percentage

## Troubleshooting

### Problem: "Groq API Key Missing"
**Solution**: 
1. Get API key from [console.groq.com](https://console.groq.com)
2. Settings → Resume & Cover Letter Generation
3. Enter API key, click Save

### Problem: PDF not generated, only .tex file
**Possible causes**:
- LaTeX tools not installed
- LaTeX path not in system PATH
- Invalid LaTeX syntax

**Solutions**:
1. Install MiKTeX or TeX Live
2. Add to PATH if needed
3. Check log file for specific LaTeX errors
4. Manually compile: `pdflatex filename.tex` in command line

### Problem: Quality of tailored content is poor
**Solution**:
1. Improve base resume content (more details, keywords)
2. Ensure base cover letter is well-written
3. Check that job description was fetched correctly
4. Try different Groq API keys or models

### Problem: "Could not extract description from URL"
**Possible causes**:
- Job posting requires authentication
- Website blocking web scraping
- URL format not recognized

**Solutions**:
1. Manually copy job description from posting
2. Edit job in database to add description
3. Use Indeed or LinkedIn format (better support)

### Problem: Cover letter not extracted from DOCX
**Solution**:
1. Ensure DOCX file is not corrupted
2. Check that file contains text (not scanned images)
3. Try re-saving DOCX in Word and try again

## Advanced Use Cases

### Custom LaTeX Template
1. Create your own `.tex` or `.txt` file with LaTeX code
2. Include sections like:
   ```latex
   \section{Experience}
   % Experience details will be tailored here
   
   \section{Skills}
   % Skills will be tailored here
   ```
3. Point Settings to this file
4. System will preserve structure and tailor content

### Batch Processing (Future)
Currently processes one job at a time. For batch processing:
1. Keep files saved in `GENERATED_DIR`
2. Manually copy/edit .tex files for multiple applications
3. Or script generation using the functions

### Integration with LaTeX Overleaf
1. Generate tailored .tex file
2. Upload to [Overleaf](https://overleaf.com)
3. Compile with full LaTeX environment
4. Get professional PDF with custom formatting

## Performance Notes

- **Groq API calls**: ~10-20 seconds each (resume + cover letter)
- **LaTeX compilation**: ~5-15 seconds per resume
- **Web scraping**: ~5-10 seconds per job URL
- **Total generation per job**: ~20-45 seconds (first time)
- **Subsequent views**: ~5-15 seconds (PDF compilation cache)

## Database Schema

New/Modified columns in `jobs` table:
```sql
generated_resume_path TEXT,    -- Path to .tex file or PDF
generated_cover_path TEXT,     -- Path to .txt or PDF
match_score_resume REAL,       -- 0-100 similarity score
match_score_cover REAL         -- 0-100 similarity score
```

Querying examples:
```sql
-- Find jobs with generated documents
SELECT id, company, title FROM jobs 
WHERE generated_resume_path IS NOT NULL;

-- Find high-quality matches
SELECT id, company, title, match_score_resume 
FROM jobs 
WHERE match_score_resume > 80 
ORDER BY match_score_resume DESC;

-- Find jobs applied to with generated docs
SELECT id, company, generated_resume_path 
FROM jobs 
WHERE status = 'Applied' 
AND generated_resume_path IS NOT NULL;
```

## See Also

- [Groq API Documentation](https://console.groq.com/docs)
- [LaTeX Project](https://www.latex-project.org/)
- [MiKTeX Homepage](https://miktex.org/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)
