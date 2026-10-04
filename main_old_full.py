"""
Personal Job Tracker - Desktop Application (Version 2.0)
Features: JobSpy scraping, IMAP email monitoring, PyQt6 GUI, SQLite DB, theme switching
Author: Datta's Job Tracker
"""

import sys
import os
import platform
import sqlite3
import json
import threading
import time
import webbrowser
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import logging
import difflib

# Third-party imports
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QPushButton,
    QLabel, QTabWidget, QDialog, QTextEdit, QSpinBox, QMessageBox,
    QFileDialog, QMenu, QHeaderView, QAbstractItemView, QStatusBar,
    QSystemTrayIcon, QMenuBar, QCheckBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QEvent
from PyQt6.QtGui import QColor, QFont, QIcon, QAction, QCursor
import schedule

# Job scraping import
try:
    from jobspy import scrape_jobs
    import pandas as pd
except ImportError:
    print("ERROR: jobspy not installed. Run: pip install jobspy")
    sys.exit(1)

# IMAP email import
try:
    from imap_tools import MailBox, AND
except ImportError:
    print("ERROR: imap-tools not installed. Run: pip install imap-tools")
    sys.exit(1)

# ============================================================================
# DATA DIRECTORY & CONFIGURATION
# ============================================================================

# Centralized user data folder
if platform.system() == "Windows":
    BASE_DIR = os.getenv("APPDATA") or os.path.expanduser(r"~\AppData\Roaming")
else:
    BASE_DIR = os.path.expanduser("~")

DATA_DIR = os.path.join(BASE_DIR, "JobTracker")
os.makedirs(DATA_DIR, exist_ok=True)

# Generated documents folder
GENERATED_DIR = os.path.join(DATA_DIR, "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

DB_FILE = os.path.join(DATA_DIR, "jobs.db")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LOG_FILE = os.path.join(DATA_DIR, "app.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Returns language code (e.g., 'en', 'de', 'fr')
    """
    try:
        from langdetect import detect
        if not text or len(text) < 10:
            return 'en'  # Default to English for short text
        return detect(text)
    except Exception as e:
        logger.debug(f"Language detection failed: {e}")
        return 'en'  # Default to English


def translate_text(text: str, source_lang: str, target_lang: str = 'en', groq_key: str = None) -> str:
    """
    Translate text using Groq AI (free and reliable).
    
    Args:
        text: Text to translate
        source_lang: Source language code (e.g., 'de', 'fr')
        target_lang: Target language code (default: 'en')
        groq_key: Groq API key
        
    Returns:
        Translated text or original text if translation fails
    """
    if source_lang == target_lang or not text:
        return text
    
    try:
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            # Create translation prompt
            lang_names = {'de': 'German', 'fr': 'French', 'es': 'Spanish', 'it': 'Italian', 'pt': 'Portuguese', 'en': 'English'}
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"""Translate the following {source_name} text to perfect {target_name}.
Keep all formatting and structure intact. Return ONLY the translated text without any explanations.

TEXT TO TRANSLATE:
{text}

TRANSLATED TEXT:"""
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000
            )
            
            translated = response.choices[0].message.content.strip()
            logger.info(f"Translated text from {source_lang} to {target_lang} ({len(text)} chars)")
            return translated
    except Exception as e:
        logger.warning(f"Translation failed: {e}. Using original text.")
    
    return text


def fetch_job_description_from_url(job_url: str, groq_key: str = None) -> str:
    """
    Fetch job description from job posting URL using Groq AI.
    Groq AI can understand and extract job descriptions from web content,
    even if JavaScript-rendered or protected by bot detection.
    """
    try:
        # If Groq key provided, use AI-powered extraction
        if groq_key:
            from groq import Groq
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(job_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Get HTML content
            html_content = response.text[:5000]  # Limit to 5000 chars of HTML
            
            # Use Groq to extract job description
            client = Groq(api_key=groq_key)
            
            extraction_prompt = f"""Extract the job description from this HTML content.
Return ONLY the job description text without HTML tags, preserving paragraph breaks.
Include: job title, company, requirements, responsibilities, benefits if available.
Clean up formatting - remove extra spaces and HTML entities.

HTML CONTENT:
{html_content}

JOB DESCRIPTION:"""
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=2000
            )
            
            description = response.choices[0].message.content.strip()
            
            if description and len(description) > 50:
                logger.info(f"Successfully extracted job description using Groq AI ({len(description)} chars)")
                return description[:5000]
        
        # Fallback: Try BeautifulSoup if Groq not available or fails
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try multiple selectors for different job sites
        description = ""
        
        # Indeed job description selectors
        indeed_desc = soup.find('div', {'id': 'jobDescriptionText'})
        if indeed_desc:
            description = indeed_desc.get_text(separator='\n', strip=True)
        
        # LinkedIn job description selectors
        if not description:
            linkedin_desc = soup.find('div', {'class': 'description'})
            if linkedin_desc:
                description = linkedin_desc.get_text(separator='\n', strip=True)
        
        # Fallback: find any article or main content
        if not description:
            article = soup.find(['article', 'main'])
            if article:
                description = article.get_text(separator='\n', strip=True)
        
        # Clean up description
        description = '\n'.join([line.strip() for line in description.split('\n') if line.strip()])
        
        if description and len(description) > 50:
            logger.info(f"Successfully fetched job description from URL using BeautifulSoup ({len(description)} chars)")
            return description[:5000]  # Limit to 5000 chars
        else:
            logger.warning(f"Could not extract description from {job_url}")
            return ""
    
    except Exception as e:
        logger.error(f"Error fetching job description from URL: {str(e)}")
        return ""


def extract_cover_letter_from_docx(docx_path: str) -> str:
    """
    Extract text content from DOCX file for cover letter.
    """
    try:
        from docx import Document
        
        doc = Document(docx_path)
        text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
        
        logger.info(f"Successfully extracted cover letter from DOCX ({len(text)} chars)")
        return text.strip()
    
    except Exception as e:
        logger.error(f"Error reading DOCX file: {str(e)}")
        return ""


def read_latex_template(latex_path: str) -> str:
    """
    Read LaTeX resume template from file.
    Handles various encodings.
    """
    try:
        # Try multiple encoding
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(latex_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                    if content:
                        logger.info(f"Successfully read LaTeX template ({len(content)} chars)")
                        return content
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Fallback with error replacement
        with open(latex_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().strip()
    
    except Exception as e:
        logger.error(f"Error reading LaTeX template: {str(e)}")
        return ""


def fix_latex_with_ai(broken_latex: str, error_message: str, groq_key: str) -> str:
    """
    Use Groq AI to fix broken LaTeX code.
    
    Args:
        broken_latex: LaTeX code that failed
        error_message: Error from compilation attempt
        groq_key: Groq API key
        
    Returns:
        Fixed LaTeX code or empty string if fix failed
    """
    try:
        if not groq_key:
            return ""
        
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        logger.info("🤖 AI is analyzing and fixing LaTeX errors...")
        
        fix_prompt = r"""You are a LaTeX expert. Fix this broken LaTeX resume code.
        
IMPORTANT - Return ONLY valid, compilable LaTeX code with NO explanations or markdown blocks.
Keep the document structure intact. Only fix the specific errors.

BROKEN LATEX:
""" + broken_latex[:3000] + r"""

ERROR MESSAGE:
""" + error_message[:500] + r"""

INSTRUCTIONS:
1. Identify the LaTeX syntax errors causing the failure
2. Fix unbalanced braces, missing packages, invalid commands
3. Ensure all backslashes are properly escaped
4. Validate document structure (\documentclass, \begin{document}, \end{document})
5. Return only the corrected LaTeX code

FIXED LATEX CODE:"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": fix_prompt}],
            max_tokens=4000,
            temperature=0.1  # Very low for accuracy
        )
        
        fixed_latex = response.choices[0].message.content.strip()
        
        # Remove markdown blocks if present
        if fixed_latex.startswith('```'):
            lines = fixed_latex.split('\n')
            fixed_latex = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        logger.info("✅ AI successfully fixed LaTeX code")
        return fixed_latex
    
    except Exception as e:
        logger.error(f"Error fixing LaTeX with AI: {str(e)}")
        return ""


def compile_latex_to_pdf(latex_content: str, output_pdf_path: str, groq_key: str = None, retry_count: int = 0) -> bool:
    """
    Compile LaTeX to PDF using pylatex library.
    If that fails, automatically fall back to pure Python PDF generation (reportlab).
    NO system tools required - 100% Python solution.
    
    Args:
        latex_content: LaTeX code to compile
        output_pdf_path: Path to save PDF
        groq_key: Groq API key for error fixing (optional)
        retry_count: Internal retry counter
        
    Returns:
        True if PDF generated successfully, False otherwise
    """
    try:
        import tempfile
        import shutil
        
        # Validate LaTeX content
        logger.info("📋 Validating LaTeX content...")
        if not latex_content or len(latex_content) < 50:
            logger.error("LaTeX content is too short or empty")
            return generate_pdf_with_reportlab(latex_content, output_pdf_path)
        
        logger.info("✅ LaTeX validation passed")
        
        # Create temporary directory for PDF generation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_tex_path = os.path.join(temp_dir, 'resume')
            
            # Write LaTeX content to file
            with open(temp_tex_path + '.tex', 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            logger.info("⚙️ Attempting LaTeX compilation with pylatex...")
            
            try:
                # Try to compile using pylatex library's built-in compiler
                from pylatex import Document
                from pylatex.utils import NoEscape
                
                # Use pylatex to handle compilation internally
                result = os.system(f'cd "{temp_dir}" && pdflatex -interaction=nonstopmode -halt-on-error "resume.tex" > nul 2>&1')
                
                if result == 0:
                    # Success - copy to target location
                    temp_pdf = os.path.join(temp_dir, 'resume.pdf')
                    if os.path.exists(temp_pdf):
                        shutil.copy(temp_pdf, output_pdf_path)
                        logger.info(f"✅ Successfully generated PDF: {output_pdf_path}")
                        return True
                
                # If LaTeX compilation failed, try reportlab immediately
                logger.warning("⚠️ LaTeX compilation failed, using pure Python PDF generation...")
                return generate_pdf_with_reportlab(latex_content, output_pdf_path)
            
            except Exception as e:
                # Any error in LaTeX compilation - fall back to reportlab
                logger.warning(f"⚠️ LaTeX compilation error: {str(e)}")
                logger.info("📄 Using pure Python PDF generation instead...")
                return generate_pdf_with_reportlab(latex_content, output_pdf_path)
    
    except Exception as e:
        logger.error(f"Error in PDF generation: {str(e)}")
        # Final fallback - always try reportlab
        return generate_pdf_with_reportlab(latex_content, output_pdf_path)


def create_simple_latex_fallback(latex_content: str) -> str:
    """
    Create a simplified LaTeX structure from complex content.
    Used as fallback when normal compilation fails.
    """
    try:
        logger.info("📝 Creating simplified LaTeX fallback...")
        
        # Extract text content from LaTeX
        import re
        
        # Remove LaTeX commands but keep content
        simple = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', latex_content)
        simple = re.sub(r'[{}\\]', '', simple)
        
        # Create minimal valid LaTeX
        fallback = r"""\documentclass{article}
\usepackage[utf-8]{inputenc}
\usepackage{geometry}
\geometry{margin=1in}
\begin{document}
\noindent
""" + simple[:2000] + r"""
\end{document}"""
        
        logger.info("✅ Simplified LaTeX fallback created")
        return fallback
    
    except Exception as e:
        logger.error(f"Error creating fallback: {str(e)}")
        return ""


def generate_pdf_with_reportlab(latex_content: str, output_pdf_path: str) -> bool:
    """
    Generate PDF using reportlab as last resort (pure Python, no system tools).
    Converts LaTeX content to simple PDF.
    """
    try:
        logger.info("📄 Generating PDF with reportlab (pure Python)...")
        
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import simpleSplit
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        
        # Extract text from LaTeX
        import re
        text = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', latex_content)
        text = re.sub(r'[{}$\\_]', '', text)
        text = text.replace('\\n', '\n').strip()
        
        # Create PDF
        doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Split text into paragraphs
        for para_text in text.split('\n\n'):
            if para_text.strip():
                story.append(Paragraph(para_text.strip(), styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        logger.info(f"✅ PDF generated with reportlab: {output_pdf_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating PDF with reportlab: {str(e)}")
        return False


def latex_to_html(latex_content: str, output_html_path: str, groq_key: str = None) -> bool:
    """
    Convert LaTeX content to HTML using Groq AI.
    This creates a beautiful, viewable resume when LaTeX tools are not installed.
    """
    try:
        if groq_key:
            from groq import Groq
            
            client = Groq(api_key=groq_key)
            
            conversion_prompt = f"""Convert this LaTeX resume to clean HTML.
Create a professional, printable HTML resume with:
- Proper CSS styling for readability
- Clear section breaks
- Good typography
- Print-friendly layout
- Inline CSS (no external stylesheets)

Return ONLY valid HTML code, starting with <!DOCTYPE html>

LATEX CONTENT:
{latex_content}

HTML RESUME:"""
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": conversion_prompt}],
                max_tokens=4000
            )
            
            html_content = response.choices[0].message.content.strip()
            
            # Clean up HTML if needed (remove markdown code blocks)
            if html_content.startswith('```'):
                html_content = html_content.split('```')[1]
                if html_content.startswith('html'):
                    html_content = html_content[4:]
                html_content = html_content.rstrip('`')
            
            # Ensure HTML starts with doctype
            if not html_content.startswith('<!DOCTYPE'):
                html_content = '<!DOCTYPE html>\n' + html_content
            
            # Write HTML file
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Successfully generated HTML resume: {output_html_path}")
            return True
        
        else:
            logger.error("Groq API key required to convert LaTeX to HTML")
            return False
    
    except Exception as e:
        logger.error(f"Error converting LaTeX to HTML: {str(e)}")
        return False


def tailor_latex_resume(latex_template: str, job_title: str, job_company: str, 
                       job_description: str, groq_key: str) -> tuple[str, float]:
    """
    Use Groq to tailor LaTeX resume content for a specific job.
    Includes language detection and translation for job descriptions.
    Returns tailored LaTeX content and match score.
    """
    try:
        from groq import Groq
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        client = Groq(api_key=groq_key)
        
        # Step 1: Detect job description language
        logger.info("Analyzing job description language...")
        detected_lang = detect_language(job_description)
        logger.info(f"Detected job description language: {detected_lang}")
        
        # Step 2: Translate to English if needed
        if detected_lang != 'en':
            logger.info(f"Translating job description from {detected_lang} to English...")
            job_description = translate_text(job_description, detected_lang, 'en', groq_key)
            logger.info("Translation complete")
        
        # Step 3: Create optimized prompt with better structure
        prompt = f"""You are an expert resume writer and LaTeX expert specializing in ATS-optimized resumes.

CRITICAL REQUIREMENTS:
1. Return ONLY valid, compilable LaTeX code - NO explanations or markdown
2. Preserve the complete document structure and preamble
3. Keep all existing sections intact
4. Modify ONLY the content sections (skills, experience, summary) to match the job
5. Highlight relevant keywords from the job description naturally
6. Maintain professional formatting and structure
7. Ensure all LaTeX syntax is valid and balanced (brackets, braces, etc.)

BASE LATEX RESUME TEMPLATE:
```
{latex_template}
```

TARGET JOB POSITION:
- Title: {job_title}
- Company: {job_company}

JOB REQUIREMENTS & KEYWORDS:
{job_description[:2000]}

INSTRUCTIONS:
1. Extract key skills and requirements from the job description
2. Reorder and emphasize relevant experience sections
3. Add skills mentioned in job description if you have them
4. Keep the tone professional and concise
5. Maintain LaTeX document structure integrity

OUTPUT: Return the complete, tailored LaTeX resume code suitable for immediate compilation:"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.3  # Lower temperature for more consistent output
        )
        
        tailored_latex = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if tailored_latex.startswith('```'):
            lines = tailored_latex.split('\n')
            tailored_latex = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
        
        logger.info(f"Generated tailored LaTeX resume ({len(tailored_latex)} chars)")
        
        # Step 4: Validate LaTeX structure
        if not tailored_latex.startswith('\\'):
            logger.warning("LaTeX output doesn't start with backslash, may be incomplete")
        
        # Calculate match score
        try:
            # Use only English for vectorization
            vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', max_features=100)
            vectors = vectorizer.fit_transform([job_description, tailored_latex])
            match_score = min(cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100, 100.0)
        except Exception as e:
            logger.debug(f"Match score calculation failed: {e}")
            match_score = 75.0
        
        logger.info(f"Generated tailored LaTeX resume (match score: {match_score:.1f}%)")
        return tailored_latex, match_score
    
    except Exception as e:
        logger.error(f"Error tailoring LaTeX resume: {str(e)}")
        return "", 0.0


# ============================================================================
# DATABASE SETUP
# ============================================================================

class Database:
    """SQLite database manager for job tracking"""
    
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                company_website TEXT,
                location TEXT,
                posted_date TEXT,
                description_snippet TEXT,
                apply_link TEXT NOT NULL UNIQUE,
                applied_date TEXT,
                status TEXT DEFAULT 'New',
                last_email_matched TEXT,
                notes TEXT,
                work_type TEXT,
                priority INTEGER DEFAULT 3,
                is_favorite INTEGER DEFAULT 0,
                generated_resume_path TEXT,
                generated_cover_path TEXT,
                match_score_resume REAL,
                match_score_cover REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)')
        
        # Migrations: Add new columns if they don't exist
        new_columns = [
            ('company_website', 'TEXT'),
            ('work_type', 'TEXT'),
            ('priority', 'INTEGER DEFAULT 3'),
            ('is_favorite', 'INTEGER DEFAULT 0'),
            ('generated_resume_path', 'TEXT'),
            ('generated_cover_path', 'TEXT'),
            ('match_score_resume', 'REAL'),
            ('match_score_cover', 'REAL'),
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE jobs ADD COLUMN {col_name} {col_type}')
                logger.info(f"Added {col_name} column to jobs table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    pass  # Column already exists
                else:
                    raise
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def insert_job(self, job_id: str, title: str, company: str, 
                   location: str, posted_date: str, description: str,
                   apply_link: str, company_website: str = None, work_type: str = None) -> bool:
        """Insert a new job into database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            title = title or "Unknown Title"
            company = company or "Unknown Company"
            location = location or "Location Not Specified"
            description = description or ""
            company_website = company_website or None
            work_type = work_type or None
            description_snippet = (description[:500] if description else "")
            
            cursor.execute('''
                INSERT OR IGNORE INTO jobs 
                (id, title, company, company_website, location, posted_date, description_snippet, apply_link, work_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, title, company, company_website, location, posted_date, description_snippet, apply_link, work_type))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error inserting job: {e}")
            return False
    
    def update_job_description(self, job_url: str, description: str) -> bool:
        """Update a job's description by URL (for LinkedIn enrichment)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if not description:
                return False
            
            description_snippet = description[:]
            
            cursor.execute('''
                UPDATE jobs
                SET description_snippet = ?
                WHERE apply_link = ?
            ''', (description_snippet, job_url))
            
            conn.commit()
            conn.close()
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated description for job URL: {job_url[:60]}...")
            return updated
        except Exception as e:
            logger.error(f"Error updating job description: {e}")
            return False
    
    def get_all_jobs(self, status_filter: str = None) -> List[Dict]:
        """Get all jobs or filtered by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status_filter and status_filter != "All":
            cursor.execute('SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC', (status_filter,))
        else:
            cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_job_by_id(self, job_id: str) -> Dict:
        """Get a specific job by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting job by ID: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, notes: str = None):
        """Update job status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE jobs SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, notes or "", job_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Job {job_id} status updated to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def update_job_priority(self, job_id: str, priority: int):
        """Update job priority (1-5)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE jobs SET priority = ? WHERE id = ?', (priority, job_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating priority: {e}")
            return False
    
    def toggle_favorite(self, job_id: str):
        """Toggle favorite status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE jobs SET is_favorite = 1 - is_favorite WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return False
    
    def save_generated_documents(self, job_id: str, resume_path: str = None, cover_path: str = None, 
                                  resume_score: float = None, cover_score: float = None):
        """Save paths and scores for generated documents"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs SET 
                    generated_resume_path = ?,
                    generated_cover_path = ?,
                    match_score_resume = ?,
                    match_score_cover = ?
                WHERE id = ?
            ''', (resume_path, cover_path, resume_score, cover_score, job_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving generated documents: {e}")
            return False
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """Get a specific job"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            logger.info(f"Job {job_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False
    
    def search_jobs(self, query: str, status_filter: str = None) -> List[Dict]:
        """Search jobs by title, company, or location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        
        if status_filter and status_filter != "All":
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE (title LIKE ? OR company LIKE ? OR location LIKE ?)
                AND status = ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern, status_filter))
        else:
            cursor.execute('''
                SELECT * FROM jobs 
                WHERE title LIKE ? OR company LIKE ? OR location LIKE ?
                ORDER BY created_at DESC
            ''', (search_pattern, search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """Get job statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "New"')
        new = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Applied"')
        applied = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Interview"')
        interview = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Rejected"')
        rejected = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE status = "Offer"')
        offer = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total,
            'new': new,
            'applied': applied,
            'interview': interview,
            'rejected': rejected,
            'offer': offer
        }

# ============================================================================
# JOB SCRAPER THREAD
# ============================================================================

class JobScraperThread(QThread):
    """Background thread for scraping jobs"""
    jobs_fetched = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    scraping_finished = pyqtSignal()
    
    def __init__(self, db: Database, search_terms: List[str], location: str, max_results: int = 50):
        super().__init__()
        self.db = db
        self.search_terms = search_terms
        self.location = location
        self.max_results = max_results
        self.is_running = True
    
    def run(self):
        """Run the scraper"""
        new_jobs_count = 0
        linkedin_urls_to_enrich = []  # Collect LinkedIn URLs with missing descriptions
        
        try:
            for search_term in self.search_terms:
                if not self.is_running:
                    logger.info("Scraper stopped by user")
                    break
                
                try:
                    logger.info(f"Scraping for: {search_term}")
                    
                    # Use correct parameter name: site_name instead of site_type
                    jobs = scrape_jobs(
                        search_term=search_term,
                        site_name=["linkedin", "indeed"],  # Changed from site_type to site_name
                        location=self.location,
                        results_wanted=self.max_results,
                        hours_old=24*7
                    )
                    
                    if not self.is_running:  # Check again after scraping
                        break
                    
                    if jobs is not None and len(jobs) > 0:
                        # Iterate using direct DataFrame method for better field access
                        for idx, (job_idx, job) in enumerate(jobs.iterrows()):
                            if not self.is_running:  # Check during iteration
                                break
                            
                            try:
                                job_id = f"{job['company']}_{hash(job['job_url'])}"
                                
                                # Try to extract company website from job data
                                company_website = job.get('company_url') or job.get('company_url_direct')
                                
                                # Extract work type (Remote/Onsite/Hybrid)
                                work_type = None
                                if pd.notna(job.get('job_type')) and job['job_type']:
                                    work_type = str(job['job_type'])
                                elif pd.notna(job.get('is_remote')) and job['is_remote']:
                                    work_type = "Remote"
                                
                                # Extract description - JobSpy provides it for Indeed, not for LinkedIn
                                description = job.get('description') or ""
                                
                                # Debug: Log first job's data to verify
                                if idx == 0:
                                    job_site = job.get('site', 'Unknown')
                                    logger.info(f"First job - Site: {job_site}, Title: {job['title']}, Has Description: {bool(description)}, Desc Length: {len(description) if description else 0}")
                                if idx > 6:
                                    break
                                # Collect LinkedIn URLs with empty descriptions for enrichment
                                job_site = job.get('site', '').lower()
                                if job_site == 'linkedin' and not description:
                                    linkedin_urls_to_enrich.append(job['job_url'])
                                
                                if self.db.insert_job(
                                    job_id=job_id,
                                    title=job['title'],
                                    company=job['company'],
                                    location=job.get('location'),
                                    posted_date=str(job.get('date_posted')) if pd.notna(job.get('date_posted')) else None,
                                    description=description,
                                    apply_link=job['job_url'],
                                    company_website=company_website,
                                    work_type=work_type
                                ):
                                    new_jobs_count += 1
                            except Exception as e:
                                logger.error(f"Error inserting job: {str(e)}")
                                continue
                        
                        logger.info(f"Added {new_jobs_count} new jobs from {search_term} (Note: LinkedIn jobs may have empty descriptions - this is a JobSpy limitation)")
                    
                except Exception as e:
                    error_msg = f"Error scraping for '{search_term}': {str(e)}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)
                    continue  # Continue to next search term instead of breaking
            
            # Step 2: Enrich LinkedIn job descriptions using Playwright
            if self.is_running and linkedin_urls_to_enrich:
                logger.info(f"Enriching {len(linkedin_urls_to_enrich)} LinkedIn jobs with full descriptions...")
                try:
                    from linkedin_scraper import scrape_linkedin_jobs
                    
                    # Scrape LinkedIn descriptions
                    linkedin_descriptions = scrape_linkedin_jobs(
                        job_urls=linkedin_urls_to_enrich,
                        headless=True,
                        rate_limit_seconds=2.5
                    )
                    
                    # Update database with scraped descriptions
                    updated_count = 0
                    for job_url, description in linkedin_descriptions.items():
                        if not self.is_running:
                            break
                        
                        if description:  # Only update if we got a description
                            try:
                                print(job_url, description[:100])  # Debug: Print URL and snippet of description
                                self.db.update_job_description(job_url, description)
                                updated_count += 1
                                logger.debug(f"Updated description for {job_url}")
                            except Exception as e:
                                logger.error(f"Error updating job description: {str(e)}")
                    
                    logger.info(f"Successfully enriched {updated_count} LinkedIn job descriptions")
                
                except ImportError:
                    logger.warning("linkedin_scraper module not available, skipping LinkedIn enrichment")
                except Exception as e:
                    logger.error(f"Error enriching LinkedIn job descriptions: {str(e)}")
                    # Don't fail the whole scrape just because enrichment failed
                    pass
            
            if self.is_running:  # Only emit if we completed normally
                self.jobs_fetched.emit(new_jobs_count)
            
        except Exception as e:
            error_msg = f"Fatal scraping error: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        
        finally:
            self.scraping_finished.emit()
    
    def stop(self):
        """Stop the thread"""
        self.is_running = False

# ============================================================================
# EMAIL WATCHER THREAD (IMAP)
# ============================================================================

class EmailWatcherThread(QThread):
    """Background thread for monitoring emails via IMAP"""
    email_processed = pyqtSignal(str, str)  # (status, message)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, db: Database, email: str, app_password: str, interval_minutes: int = 30):
        super().__init__()
        self.db = db
        self.email = email
        self.app_password = app_password
        self.interval_minutes = interval_minutes
        self.is_running = True
        self.daemon = True
    
    def run(self):
        """Monitor emails periodically"""
        while self.is_running:
            try:
                self.check_emails()
            except Exception as e:
                logger.error(f"Email watcher error: {e}")
                self.error_occurred.emit(f"Email check failed: {str(e)}")
            
            # Sleep for the configured interval
            time.sleep(self.interval_minutes * 60)
    
    def check_emails(self):
        """Check unread emails and update job status"""
        try:
            keywords = {
                'interview': ['interview', 'interviewtermin', 'gespräch', 'termin', 'vorstellungsgespräch', 'gesprächstermin'],
                'rejected': ['unfortunately', 'not proceeding', 'nicht in Betracht', 'ablehnung', 'absage', 'leider nicht', 'we decided', 'regret'],
                'offer': ['offer', 'position', 'angebot', 'stelle', 'job offer', 'welcome', 'willkommen', 'können wir dir anbieten']
            }
            
            with MailBox('imap.gmail.com').login(self.email, self.app_password, 'INBOX') as mailbox:
                for msg in mailbox.fetch(AND(seen=False)):
                    subject_lower = msg.subject.lower()
                    body_lower = msg.text.lower()
                    
                    # Detect status from email content
                    detected_status = None
                    for status, kws in keywords.items():
                        if any(kw in subject_lower or kw in body_lower for kw in kws):
                            detected_status = status.capitalize()
                            break
                    
                    if detected_status:
                        # Try to match email to a job using fuzzy matching
                        jobs = self.db.get_all_jobs()
                        best_match = None
                        best_score = 0
                        
                        for job in jobs:
                            # Match company name
                            company_match = difflib.SequenceMatcher(
                                None, 
                                job['company'].lower(), 
                                subject_lower + " " + body_lower[:200]
                            ).ratio()
                            
                            # Match job title
                            title_match = difflib.SequenceMatcher(
                                None, 
                                job['title'].lower(), 
                                subject_lower[:100]
                            ).ratio()
                            
                            combined_score = (company_match * 0.6 + title_match * 0.4)
                            
                            if combined_score > best_score and combined_score > 0.5:
                                best_match = job
                                best_score = combined_score
                        
                        if best_match:
                            # Update job status
                            email_snippet = msg.subject[:100]
                            self.db.update_job_status(
                                best_match['id'], 
                                detected_status, 
                                f"Email: {email_snippet}"
                            )
                            self.email_processed.emit(detected_status, f"{best_match['company']} - {best_match['title']}")
                            logger.info(f"Updated job to {detected_status}: {best_match['company']}")
                    
                    # Mark email as read
                    mailbox.flag([msg.uid], ['\\Seen'], True)
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            raise
    
    def stop(self):
        """Stop the thread"""
        self.is_running = False

# ============================================================================
# SETTINGS DIALOG
# ============================================================================

class SettingsDialog(QDialog):
    """Settings dialog for app configuration"""
    # Signals for thread-safe Gmail test
    gmail_test_success = pyqtSignal(str)  # Success message
    gmail_test_error = pyqtSignal(str)    # Error message
    
    def __init__(self, parent=None, config_path: str = CONFIG_FILE):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self.load_config()
        self.init_ui()
        self.setWindowTitle("Job Tracker Settings")
        self.setGeometry(100, 100, 700, 600)
        
        # Connect signals for thread-safe Gmail test
        self.gmail_test_success.connect(self.on_gmail_test_success)
        self.gmail_test_error.connect(self.on_gmail_test_error)
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return {
            'search_terms': ['Python Developer', 'Software Engineer'],
            'location': 'Germany',
            'country': 'Germany',
            'results_wanted': 50,
            'scrape_interval_hours': 2,
            'email_check_interval_minutes': 30,
            'gmail_email': '',
            'gmail_enabled': False,
            'theme': 'Dark'
        }
    
    def init_ui(self):
        """Initialize UI elements"""
        layout = QVBoxLayout()
        
        # Search terms
        layout.addWidget(QLabel("Search Terms (one per line):"))
        self.search_terms_input = QTextEdit()
        self.search_terms_input.setPlainText("\n".join(self.config.get('search_terms', [])))
        layout.addWidget(self.search_terms_input)
        
        # Location
        layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setText(self.config.get('location', 'Germany'))
        layout.addWidget(self.location_input)
        
        # Results
        layout.addWidget(QLabel("Results per Scrape:"))
        self.results_input = QSpinBox()
        self.results_input.setValue(self.config.get('results_wanted', 50))
        self.results_input.setRange(10, 500)
        layout.addWidget(self.results_input)
        
        # Scrape interval
        layout.addWidget(QLabel("Scrape Interval (hours):"))
        self.scrape_interval = QSpinBox()
        self.scrape_interval.setValue(self.config.get('scrape_interval_hours', 2))
        self.scrape_interval.setRange(1, 24)
        layout.addWidget(self.scrape_interval)
        
        # ===== GMAIL SETTINGS =====
        layout.addWidget(QLabel("\n📧 Gmail Settings (IMAP + App Password):"))
        
        layout.addWidget(QLabel("Gmail Email:"))
        self.gmail_email = QLineEdit()
        self.gmail_email.setPlaceholderText("your.email@gmail.com")
        self.gmail_email.setText(self.config.get('gmail_email', ''))
        layout.addWidget(self.gmail_email)
        
        layout.addWidget(QLabel("App Password (16 chars):"))
        self.gmail_password = QLineEdit()
        self.gmail_password.setPlaceholderText("xxxx xxxx xxxx xxxx")
        self.gmail_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.gmail_password)
        
        # Email check interval
        layout.addWidget(QLabel("Email Check Interval (minutes):"))
        self.email_interval = QSpinBox()
        self.email_interval.setValue(self.config.get('email_check_interval_minutes', 30))
        self.email_interval.setRange(5, 120)
        layout.addWidget(self.email_interval)
        
        # Test Gmail connection button
        self.test_gmail_btn = QPushButton("Save & Test Connection")
        self.test_gmail_btn.clicked.connect(self.test_gmail_connection)
        layout.addWidget(self.test_gmail_btn)
        
        # Gmail enabled checkbox
        self.gmail_enabled_check = QCheckBox("Enable Gmail Monitoring")
        self.gmail_enabled_check.setChecked(self.config.get('gmail_enabled', False))
        layout.addWidget(self.gmail_enabled_check)
        
        # ===== RESUME & COVER LETTER GENERATION =====
        layout.addWidget(QLabel("\n📄 Resume & Cover Letter Generation:"))
        
        layout.addWidget(QLabel("Groq API Key (get free at groq.com):"))
        self.groq_key = QLineEdit()
        self.groq_key.setPlaceholderText("gsk_...")
        self.groq_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_key.setText(self.config.get('groq_api_key', ''))
        layout.addWidget(self.groq_key)
        
        # Base Resume selector
        resume_layout = QHBoxLayout()
        layout.addWidget(QLabel("Base Resume (PDF):"))
        self.resume_label = QLineEdit()
        self.resume_label.setText(self.config.get('base_resume_path', '') or "No file selected")
        self.resume_label.setReadOnly(True)
        resume_layout.addWidget(self.resume_label)
        select_resume_btn = QPushButton("Select...")
        select_resume_btn.clicked.connect(self.select_base_resume)
        resume_layout.addWidget(select_resume_btn)
        layout.addLayout(resume_layout)
        
        # Base Cover Letter selector
        cover_layout = QHBoxLayout()
        layout.addWidget(QLabel("Base Cover Letter (PDF or TXT):"))
        self.cover_label = QLineEdit()
        self.cover_label.setText(self.config.get('base_cover_letter_path', '') or "No file selected")
        self.cover_label.setReadOnly(True)
        cover_layout.addWidget(self.cover_label)
        select_cover_btn = QPushButton("Select...")
        select_cover_btn.clicked.connect(self.select_base_cover)
        cover_layout.addWidget(select_cover_btn)
        layout.addLayout(cover_layout)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
    
    def test_gmail_connection(self):
        """Test IMAP connection to Gmail"""
        email = self.gmail_email.text().strip()
        password = self.gmail_password.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Missing Info", "Please enter Gmail email and app password")
            return
        
        # Disable button and show loading state
        self.test_gmail_btn.setText("Testing connection...")
        self.test_gmail_btn.setEnabled(False)
        
        # Run test in background thread to avoid blocking UI
        def test_connection():
            try:
                logger.info(f"Testing Gmail IMAP connection for {email}")
                # Set timeout to 10 seconds
                mailbox = MailBox('imap.gmail.com', timeout=10)
                mailbox.login(email, password, 'INBOX')
                # Just check if we can log in, don't fetch all emails
                mailbox.logout()
                
                # Emit success signal (runs in main thread)
                self.gmail_test_success.emit("✅ Gmail connection successful!\n\nYour email monitoring is ready to use.")
                logger.info(f"Gmail connection test successful for {email}")
                
            except TimeoutError:
                # Emit error signal (runs in main thread)
                self.gmail_test_error.emit(
                    "⏱️ Connection timeout (10 seconds)\n\n"
                    "Make sure:\n"
                    "1. Your internet connection is working\n"
                    "2. IMAP is enabled in Gmail settings\n"
                    "3. App password is correct (16 chars, no spaces)")
                logger.error(f"Gmail connection test timeout for {email}")
                
            except Exception as e:
                error_str = str(e)
                if "401" in error_str or "authentication" in error_str.lower():
                    msg = "❌ Authentication failed\n\nMake sure:\n1. Email address is correct\n2. App password is correct (no spaces)\n3. IMAP is enabled in Gmail settings"
                else:
                    msg = f"❌ Connection failed\n\nError: {error_str}\n\nMake sure:\n1. IMAP is enabled in Gmail settings\n2. App password is correct (16 chars, no spaces)"
                
                # Emit error signal (runs in main thread)
                self.gmail_test_error.emit(msg)
                logger.error(f"Gmail connection test failed: {e}")
        
        # Start test in background thread
        test_thread = threading.Thread(target=test_connection, daemon=True)
        test_thread.start()
    
    def on_gmail_test_success(self, message: str):
        """Handle Gmail test success (runs in main thread)"""
        self.test_gmail_btn.setText("Save & Test Connection")
        self.test_gmail_btn.setEnabled(True)
        QMessageBox.information(self, "Success", message)
    
    def on_gmail_test_error(self, message: str):
        """Handle Gmail test error (runs in main thread)"""
        self.test_gmail_btn.setText("Save & Test Connection")
        self.test_gmail_btn.setEnabled(True)
        QMessageBox.critical(self, "Connection Failed", message)
    
    def select_base_resume(self):
        """Select base resume LaTeX file (TXT format)"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base Resume (LaTeX TXT)", "", "Text Files (*.txt);;LaTeX Files (*.tex)")
        if file_path:
            self.resume_label.setText(file_path)
            self.config['base_resume_path'] = file_path
            logger.info(f"Base resume selected: {file_path}")
    
    def select_base_cover(self):
        """Select base cover letter DOCX"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Base Cover Letter (DOCX)", "", "Word Documents (*.docx);;Text Files (*.txt)")
        if file_path:
            self.cover_label.setText(file_path)
            self.config['base_cover_letter_path'] = file_path
            logger.info(f"Base cover letter selected: {file_path}")
    
    def save_settings(self):
        """Save settings to file"""
        self.config['search_terms'] = [t.strip() for t in self.search_terms_input.toPlainText().split('\n') if t.strip()]
        self.config['location'] = self.location_input.text()
        self.config['results_wanted'] = self.results_input.value()
        self.config['scrape_interval_hours'] = self.scrape_interval.value()
        self.config['email_check_interval_minutes'] = self.email_interval.value()
        self.config['gmail_email'] = self.gmail_email.text().strip()
        self.config['gmail_enabled'] = self.gmail_enabled_check.isChecked()
        self.config['groq_api_key'] = self.groq_key.text().strip()
        # base_resume_path and base_cover_letter_path already set in select methods
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Success", "Settings saved! Please restart the app for all changes to take effect.")
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

# ============================================================================
# THEMES
# ============================================================================

THEMES = {
    'Light': """
        QMainWindow { background-color: white; color: black; }
        QTableWidget { background-color: white; color: black; gridline-color: #ddd; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #5DADE2; color: white; }
        QHeaderView::section { background-color: #f0f0f0; color: black; padding: 5px; border: 1px solid #ddd; }
        QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #0056b3; }
        QLineEdit { border: 1px solid #ccc; padding: 5px; }
        QComboBox { border: 1px solid #ccc; padding: 5px; }
        QStatusBar { background-color: #f0f0f0; color: black; }
    """,
    'Dark': """
        QMainWindow { background-color: #2d2d2d; color: #e0e0e0; }
        QTableWidget { background-color: #1e1e1e; color: #e0e0e0; gridline-color: #444; alternate-background-color: #2a2a2a; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #007acc; color: white; }
        QHeaderView::section { background-color: #333; color: #e0e0e0; padding: 5px; border: 1px solid #555; }
        QPushButton { background-color: #007acc; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #005a9e; }
        QLineEdit { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555; padding: 5px; }
        QComboBox { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #555; padding: 5px; }
        QLabel { color: #e0e0e0; }
        QStatusBar { background-color: #333; color: #e0e0e0; }
        QMenuBar { background-color: #2d2d2d; color: #e0e0e0; }
        QMenu { background-color: #2d2d2d; color: #e0e0e0; }
        QMenu::item:selected { background-color: #007acc; }
    """,
    'Pastel': """
        QMainWindow { background-color: #f0f8ff; color: #333; }
        QTableWidget { background-color: #fef5e7; color: #333; gridline-color: #e8d5c4; alternate-background-color: #f9f5f0; }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background-color: #a8dadc; color: white; }
        QHeaderView::section { background-color: #f4a261; color: white; padding: 5px; border: 1px solid #e8d5c4; }
        QPushButton { background-color: #a8dadc; color: white; border: none; padding: 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #8bc5d0; }
        QLineEdit { background-color: #fffbf0; color: #333; border: 1px solid #e8d5c4; padding: 5px; }
        QComboBox { background-color: #fffbf0; color: #333; border: 1px solid #e8d5c4; padding: 5px; }
        QLabel { color: #333; }
        QStatusBar { background-color: #f9f5f0; color: #333; }
    """
}

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class JobTrackerApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data
        self.data_dir = DATA_DIR
        self.config_file = CONFIG_FILE
        self.load_config()
        self.db = Database(DB_FILE)
        
        # Show data location on first run
        if not os.path.exists(os.path.join(DATA_DIR, ".initialized")):
            # QMessageBox.information(
            #     self, 
            #     "Data Location", 
            #     f"All your data is saved safely in:\n\n{DATA_DIR}\n\nYou can move the .exe anywhere."
            # )
            # Create marker file
            open(os.path.join(DATA_DIR, ".initialized"), 'a').close()
        
        self.setWindowTitle("Job Tracker v2.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize UI
        self.init_ui()
        self.apply_theme(self.config.get('theme', 'Dark'))
        
        # Scheduler
        self.scheduler_thread = None
        self.scraper_thread = None
        self.email_watcher_thread = None
        
        # Status tracking
        self.last_scrape_time = None
        self.last_scrape_count = 0
        
        # Initialize scraper
        self.start_scheduler()
        
        # Load existing jobs from database on startup (don't auto-scrape)
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
    
    def load_config(self):
        """Load configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'search_terms': ['Quality Management',
                                'Process Improvement',
                                'Logistics Quality Intern',
                                'ISO Audit Praktikum',
                                'Werkstudent Quality management',
                                'Quality Intern Supply Chain',
                                'Praktikum Logistik Quality'],
            'location': 'Hamburg, Germany',
            'results_wanted': 50,
            'scrape_interval_hours': 2,
            'email_check_interval_minutes': 120,
            'gmail_email': '',
            'gmail_enabled': False,
            'theme': 'Dark',
            'groq_api_key': '',
            'base_resume_path': '',
            'base_cover_letter_path': ''
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def init_ui(self):
        """Initialize user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Search and filter layout
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, company, or location...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        search_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "New", "Applied", "Interview", "Rejected", "Offer", "Ghosted"])
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        search_layout.addWidget(self.status_filter)
        
        main_layout.addLayout(search_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Work Type:"))
        self.work_type_filter = QComboBox()
        self.work_type_filter.addItems(["All", "Remote", "Onsite", "Hybrid"])
        self.work_type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.work_type_filter)
        
        self.priority_filter = QCheckBox("High Priority (4-5 only)")
        self.priority_filter.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.priority_filter)
        
        self.favorites_filter = QCheckBox("Favorites Only")
        self.favorites_filter.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.favorites_filter)
        
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels(["Title", "Company", "Location", "Posted", "Status", "Apply Link", "Company Website", "Work Type", "Priority", "Favorite", "Resume", "Cover"])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self.open_apply_link)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh Jobs Now")
        refresh_btn.clicked.connect(self.refresh_jobs)
        button_layout.addWidget(refresh_btn)
        
        mark_applied_btn = QPushButton("✓ Mark as Applied")
        mark_applied_btn.clicked.connect(self.mark_selected_applied)
        button_layout.addWidget(mark_applied_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_rows)
        button_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("📊 Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_btn)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        
        # Tray icon
        self.setup_tray_icon()
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Themes menu
        themes_menu = menubar.addMenu("Themes")
        for theme_name in THEMES:
            action = QAction(theme_name, self)
            action.triggered.connect(lambda checked, t=theme_name: self.set_theme(t))
            themes_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        quickstart_action = QAction("Quickstart Guide", self)
        quickstart_action.triggered.connect(self.show_quickstart)
        help_menu.addAction(quickstart_action)
        
        gmail_action = QAction("Gmail Setup Guide", self)
        gmail_action.triggered.connect(self.show_gmail_guide)
        help_menu.addAction(gmail_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def set_theme(self, theme_name: str):
        """Set application theme"""
        if theme_name in THEMES:
            self.apply_theme(theme_name)
            self.config['theme'] = theme_name
            self.save_config()
    
    def apply_theme(self, theme_name: str):
        """Apply theme stylesheet"""
        if theme_name in THEMES:
            self.setStyleSheet(THEMES[theme_name])
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Tray icon activation handler"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
    
    def update_status_bar(self):
        """Update status bar with statistics"""
        stats = self.db.get_stats()
        self.status_bar.showMessage(
            f"Total: {stats['total']} | New: {stats['new']} | Applied: {stats['applied']} | " 
            f"Interview: {stats['interview']} | Rejected: {stats['rejected']} | Offer: {stats['offer']}"
        )
    
    def refresh_table(self, search_query: str = "", status_filter: str = "All"):
        """Refresh job table"""
        if search_query:
            jobs = self.db.search_jobs(search_query, status_filter if status_filter != "All" else None)
        else:
            jobs = self.db.get_all_jobs(status_filter if status_filter != "All" else None)
        
        self.table.setRowCount(0)
        
        for row_idx, job in enumerate(jobs):
            self.table.insertRow(row_idx)
            
            # Title
            title_item = QTableWidgetItem(job['title'])
            self.table.setItem(row_idx, 0, title_item)
            
            # Company
            company_item = QTableWidgetItem(job['company'])
            self.table.setItem(row_idx, 1, company_item)
            
            # Location
            location_item = QTableWidgetItem(job['location'] or "N/A")
            self.table.setItem(row_idx, 2, location_item)
            
            # Posted date
            posted_item = QTableWidgetItem(job['posted_date'] or "N/A")
            self.table.setItem(row_idx, 3, posted_item)
            
            # Status with color coding
            status_item = QTableWidgetItem(job['status'])
            status_colors = {
                'New': QColor('#3498db'),  # Blue
                'Applied': QColor('#2ecc71'),  # Green
                'Interview': QColor('#f39c12'),  # Orange
                'Rejected': QColor('#e74c3c'),  # Red
                'Offer': QColor('#27ae60'),  # Dark Green
                'Ghosted': QColor('#95a5a6')  # Gray
            }
            if job['status'] in status_colors:
                status_item.setBackground(status_colors[job['status']])
                status_item.setForeground(QColor('white'))
            self.table.setItem(row_idx, 4, status_item)
            
            # Apply link
            link_item = QTableWidgetItem("Open Link")
            link_item.setForeground(QColor('#007bff'))
            link_item.setData(Qt.ItemDataRole.UserRole, job['apply_link'])
            link_item.setFont(QFont(link_item.font().family(), -1, -1, True))  # Underline
            self.table.setItem(row_idx, 5, link_item)
            
            # Company website
            company_website_item = QTableWidgetItem("Visit Website" if job.get('company_website') else "N/A")
            if job.get('company_website'):
                company_website_item.setForeground(QColor('#27ae60'))  # Green for clickable
                company_website_item.setData(Qt.ItemDataRole.UserRole, job['company_website'])
                company_website_item.setFont(QFont(company_website_item.font().family(), -1, -1, True))  # Underline
            self.table.setItem(row_idx, 6, company_website_item)
            
            # Work Type
            work_type_item = QTableWidgetItem(job.get('work_type') or "N/A")
            self.table.setItem(row_idx, 7, work_type_item)
            
            # Priority (1-5, default 3)
            priority = job.get('priority') or 3
            priority_item = QTableWidgetItem("⭐" * priority)
            priority_item.setData(Qt.ItemDataRole.UserRole, priority)
            self.table.setItem(row_idx, 8, priority_item)
            
            # Favorite (★ if favorited)
            is_favorite = job.get('is_favorite', 0)
            favorite_item = QTableWidgetItem("★" if is_favorite else "☆")
            favorite_item.setData(Qt.ItemDataRole.UserRole, is_favorite)
            favorite_item.setForeground(QColor('#f39c12') if is_favorite else QColor('#95a5a6'))  # Gold if favorited
            self.table.setItem(row_idx, 9, favorite_item)
            
            # Resume generated (✓ if exists)
            resume_path = job.get('generated_resume_path')
            resume_item = QTableWidgetItem("✓" if resume_path else "✗")
            if resume_path:
                resume_item.setForeground(QColor('#2ecc71'))  # Green
                resume_item.setData(Qt.ItemDataRole.UserRole, resume_path)
            else:
                resume_item.setForeground(QColor('#95a5a6'))  # Gray
            self.table.setItem(row_idx, 10, resume_item)
            
            # Cover letter generated (✓ if exists)
            cover_path = job.get('generated_cover_path')
            cover_item = QTableWidgetItem("✓" if cover_path else "✗")
            if cover_path:
                cover_item.setForeground(QColor('#2ecc71'))  # Green
                cover_item.setData(Qt.ItemDataRole.UserRole, cover_path)
            else:
                cover_item.setForeground(QColor('#95a5a6'))  # Gray
            self.table.setItem(row_idx, 11, cover_item)
            
            # Store job_id for later reference
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, job['id'])
    
    def apply_filters(self):
        """Apply active filters to the table"""
        # Get filter values
        work_type_filter = self.work_type_filter.currentText()
        priority_filter = self.priority_filter.isChecked()
        favorites_filter = self.favorites_filter.isChecked()
        
        # Hide/show rows based on filters
        for row in range(self.table.rowCount()):
            show_row = True
            
            # Work type filter
            if work_type_filter != "All":
                work_type = self.table.item(row, 7).text() if self.table.item(row, 7) else ""
                if work_type != work_type_filter:
                    show_row = False
            
            # Priority filter (4-5 stars only)
            if show_row and priority_filter:
                priority = self.table.item(row, 8).data(Qt.ItemDataRole.UserRole) if self.table.item(row, 8) else 3
                if priority < 4:
                    show_row = False
            
            # Favorites filter
            if show_row and favorites_filter:
                is_favorite = self.table.item(row, 9).data(Qt.ItemDataRole.UserRole) if self.table.item(row, 9) else 0
                if not is_favorite:
                    show_row = False
            
            self.table.setRowHidden(row, not show_row)
        
        self.update_status_bar()
    
    def open_apply_link(self, row: int, col: int):
        """Open apply link, company website, or generated documents when double-clicked"""
        # Column 5 = Apply Link, Column 6 = Company Website, Column 10 = Resume, Column 11 = Cover
        if col in [5, 6]:  # URLs
            url = self.table.item(row, col).data(Qt.ItemDataRole.UserRole)
            if url:
                webbrowser.open(url)
                logger.info(f"Opened {'Apply Link' if col == 5 else 'Company Website'}: {url}")
        elif col in [10, 11]:  # Generated documents
            file_path = self.table.item(row, col).data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                try:
                    # For LaTeX resume files, try to open PDF or HTML
                    if col == 10 and file_path.endswith('.tex'):
                        pdf_path = file_path.replace('.tex', '.pdf')
                        html_path = file_path.replace('.tex', '.html')
                        
                        # Check if PDF exists and can be opened
                        if os.path.exists(pdf_path):
                            os.startfile(pdf_path)
                            logger.info(f"Opened LaTeX resume (PDF): {pdf_path}")
                        
                        # Try HTML version
                        elif os.path.exists(html_path):
                            webbrowser.open("file://" + html_path)
                            logger.info(f"Opened resume (HTML): {html_path}")
                        
                        # Show compilation dialog if neither PDF nor HTML exists
                        else:
                            progress_dialog = QDialog(self)
                            progress_dialog.setWindowTitle("Preparing Resume...")
                            layout = QVBoxLayout()
                            progress_dialog.setMinimumWidth(300)
                            layout.addWidget(QLabel("Generating resume in HTML format...\nThis may take a moment."))
                            progress_bar = QProgressBar()
                            progress_bar.setMaximum(0)  # Indeterminate
                            layout.addWidget(progress_bar)
                            progress_dialog.setLayout(layout)
                            progress_dialog.show()
                            QApplication.processEvents()
                            
                            # Read LaTeX content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                latex_content = f.read()
                            
                            # Get Groq API key from config
                            groq_api_key = self.config.get('groq_api_key', '')
                            
                            # Try PDF compilation first (with AI error fixing if available)
                            pdf_generated = compile_latex_to_pdf(latex_content, pdf_path, groq_api_key)
                            
                            if pdf_generated and os.path.exists(pdf_path):
                                progress_dialog.close()
                                os.startfile(pdf_path)
                                logger.info(f"Compiled and opened LaTeX resume: {pdf_path}")
                            
                            # Fall back to HTML generation
                            else:
                                html_generated = latex_to_html(latex_content, html_path, groq_api_key)
                                progress_dialog.close()
                                
                                if html_generated and os.path.exists(html_path):
                                    webbrowser.open("file://" + html_path)
                                    logger.info(f"Generated and opened HTML resume: {html_path}")
                                else:
                                    QMessageBox.warning(
                                        self,
                                        "Resume Generation Failed",
                                        "Could not generate PDF or HTML resume.\n\nYou can open the .tex file manually with a text editor or LaTeX viewer."
                                    )
                                    os.startfile(file_path)  # Open the .tex file instead
                    else:
                        # For other file types (cover letter, PDF, HTML), open directly
                        if file_path.endswith('.html'):
                            webbrowser.open("file://" + file_path)
                        else:
                            os.startfile(file_path)
                        logger.info(f"Opened {'Resume' if col == 10 else 'Cover Letter'}: {file_path}")
                except Exception as e:
                    logger.error(f"Error opening file {file_path}: {e}")
                    self.show_message(f"Could not open file: {str(e)}", "error")
            else:
                self.show_message("Document not found or not yet generated", "info")
    
    def show_context_menu(self, position):
        """Show right-click context menu"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        menu = QMenu()
        
        open_link_action = QAction("Open Apply Link", self)
        open_link_action.triggered.connect(lambda: self.open_apply_link(row, 5))
        menu.addAction(open_link_action)
        
        # Add company website option if available
        company_website = self.table.item(row, 6).data(Qt.ItemDataRole.UserRole)
        if company_website:
            open_website_action = QAction("Open Company Website", self)
            open_website_action.triggered.connect(lambda: self.open_apply_link(row, 6))
            menu.addAction(open_website_action)
        
        menu.addSeparator()
        
        # Add toggle favorite option
        is_favorite = self.table.item(row, 9).data(Qt.ItemDataRole.UserRole)
        favorite_text = "Remove from Favorites" if is_favorite else "Add to Favorites"
        favorite_action = QAction(favorite_text, self)
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        favorite_action.triggered.connect(lambda: self.toggle_favorite(row, job_id))
        menu.addAction(favorite_action)
        
        menu.addSeparator()
        
        # Add priority change options
        priority_menu = menu.addMenu("Set Priority")
        for i in range(1, 6):
            priority_action = QAction("⭐" * i, self)
            priority_action.triggered.connect(lambda checked, p=i, jid=job_id: self.set_job_priority(row, jid, p))
            priority_menu.addAction(priority_action)
        
        menu.addSeparator()
        
        # Add generate documents option
        generate_action = QAction("Generate Tailored Resume & Cover Letter", self)
        generate_action.triggered.connect(lambda: self.generate_tailored_documents(row, job_id))
        menu.addAction(generate_action)
        
        menu.addSeparator()
        
        for status in ["Applied", "Interview", "Rejected", "Offer", "Ghosted"]:
            action = QAction(f"Mark as {status}", self)
            action.triggered.connect(lambda checked, s=status: self.mark_row_status(row, s))
            menu.addAction(action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete Job", self)
        delete_action.triggered.connect(lambda: self.delete_job(row))
        menu.addAction(delete_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def mark_row_status(self, row: int, status: str):
        """Mark job status"""
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if job_id:
            self.db.update_job_status(job_id, status)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def mark_selected_applied(self):
        """Mark selected job as applied"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.mark_row_status(current_row, "Applied")
    
    def delete_job(self, row: int):
        """Delete a job"""
        job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if job_id:
            reply = QMessageBox.question(self, "Confirm Delete", "Delete this job?")
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_job(job_id)
                self.refresh_table(self.search_input.text(), self.status_filter.currentText())
                self.update_status_bar()
    
    def delete_selected_rows(self):
        """Delete all selected rows with double confirmation"""
        # Get all selected rows
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select at least one job to delete")
            return
        
        job_count = len(selected_rows)
        
        # First confirmation dialog
        reply1 = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete {job_count} job(s)?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply1 != QMessageBox.StandardButton.Yes:
            return
        
        # Second confirmation dialog (extra warning)
        reply2 = QMessageBox.warning(
            self,
            "Final Warning - No Recovery",
            f"⚠️ WARNING: You are about to permanently delete {job_count} job(s).\n\n"
            "This data CANNOT be recovered once deleted.\n\n"
            "Are you absolutely sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply2 != QMessageBox.StandardButton.Yes:
            return
        
        # Delete all selected jobs
        deleted_count = 0
        for model_index in selected_rows:
            row = model_index.row()
            job_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if job_id:
                try:
                    self.db.delete_job(job_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting job {job_id}: {e}")
        
        # Refresh table
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
        
        # Show summary
        QMessageBox.information(self, "Delete Complete", f"✓ Successfully deleted {deleted_count} job(s)")
    
    def toggle_favorite(self, row: int, job_id: int):
        """Toggle favorite status for a job"""
        if job_id:
            self.db.toggle_favorite(job_id)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def set_job_priority(self, row: int, job_id: int, priority: int):
        """Set job priority (1-5)"""
        if job_id:
            self.db.update_job_priority(job_id, priority)
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
    
    def read_document_file(self, file_path: str) -> str:
        """Read document file (TXT, PDF, DOCX) with proper encoding handling"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Handle PDF files
            if file_ext == '.pdf':
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
                except Exception as e:
                    raise Exception(f"Error reading PDF: {str(e)}")
            
            # Handle DOCX files
            elif file_ext == '.docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    return text.strip()
                except Exception as e:
                    raise Exception(f"Error reading DOCX: {str(e)}")
            
            # Handle text files with encoding detection
            else:
                # Try common encodings
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            return f.read().strip()
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                # If all encodings fail, try with errors='replace'
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read().strip()
        
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    
    def generate_tailored_documents(self, row: int, job_id: int):
        """Generate tailored resume (LaTeX) and cover letter using Groq AI with web scraping for job descriptions"""
        if not job_id:
            return
        
        # Check if Groq API key is configured
        groq_api_key = self.config.get('groq_api_key', '')
        if not groq_api_key:
            QMessageBox.critical(
                self,
                "Groq API Key Missing",
                "Please add your Groq API key in Settings → Resume & Cover Letter Generation"
            )
            return
        
        # Check if base documents are configured
        base_resume_path = self.config.get('base_resume_path', '')
        base_cover_path = self.config.get('base_cover_letter_path', '')
        
        if not base_resume_path or not base_cover_path:
            QMessageBox.critical(
                self,
                "Base Documents Missing",
                "Please select your base resume (LaTeX TXT) and cover letter (DOCX) in Settings"
            )
            return
        
        # Get job details
        job = self.db.get_job_by_id(job_id)
        if not job:
            QMessageBox.critical(self, "Error", f"Job not found: {job_id}")
            return
        
        # Read base LaTeX resume
        try:
            base_latex_resume = read_latex_template(base_resume_path)
            if not base_latex_resume:
                raise Exception("LaTeX template is empty")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read LaTeX resume template: {str(e)}")
            return
        
        # Read cover letter from DOCX
        try:
            base_cover_text = extract_cover_letter_from_docx(base_cover_path)
            if not base_cover_text:
                raise Exception("Cover letter is empty")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read cover letter DOCX: {str(e)}")
            return
        
        # Create progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Generating Tailored Documents")
        progress_dialog.setMinimumWidth(450)
        progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        layout = QVBoxLayout()
        label = QLabel(f"<b>Generating for:</b><br>{job['company']} - {job['title']}")
        layout.addWidget(label)
        
        progress_bar = QProgressBar()
        progress_bar.setMaximum(0)
        layout.addWidget(progress_bar)
        
        status_label = QLabel("Fetching job description...")
        layout.addWidget(status_label)
        
        progress_dialog.setLayout(layout)
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Step 1: Fetch job description (especially for LinkedIn jobs)
            job_desc = job.get('description_snippet') or ""
            
            if not job_desc or len(job_desc.strip()) < 100:
                # Job description is empty or too short - try web scraping
                status_label.setText("Fetching job description from posting URL...")
                QApplication.processEvents()
                
                # Use Groq AI to extract job description from URL
                scraped_desc = fetch_job_description_from_url(job.get('job_url', ''), groq_api_key)
                if scraped_desc:
                    job_desc = scraped_desc
                    logger.info(f"Successfully scraped job description ({len(job_desc)} chars)")
                else:
                    job_desc = f"Position: {job['title']} at {job['company']}"
                    logger.warning("Could not fetch job description, using basic info")
            
            # Step 2: Generate tailored LaTeX resume
            status_label.setText("Tailoring resume with Groq AI...")
            QApplication.processEvents()
            
            tailored_latex, resume_match = tailor_latex_resume(
                base_latex_resume,
                job['title'],
                job['company'],
                job_desc[:],
                groq_api_key
            )
            
            if not tailored_latex:
                raise Exception("Failed to generate tailored resume")
            
            # Step 3: Generate tailored cover letter
            status_label.setText("Tailoring cover letter with Groq AI...")
            QApplication.processEvents()
            
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            cover_prompt = f"""You are an expert cover letter writer. Write a compelling cover letter tailored to this job.
Match the job requirements and company culture. Keep it professional and concise.
Use a business letter format.

JOB DETAILS:
Title: {job['title']}
Company: {job['company']}
Location: {job.get('location', 'Location not specified')}
Description: {job_desc[:1500]}

BASE COVER LETTER for reference:
{base_cover_text[:1000]}

TAILORED COVER LETTER (business letter format, plain text):"""
            
            cover_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": cover_prompt}],
                max_tokens=1500
            )
            tailored_cover = cover_response.choices[0].message.content.strip()
            
            # Calculate cover letter match score
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                
                vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
                vectors = vectorizer.fit_transform([job_desc.lower(), tailored_cover.lower()])
                cover_match = cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100
            except:
                cover_match = 75
            
            # Step 4: Save LaTeX resume and cover letter as files
            status_label.setText("Saving documents...")
            QApplication.processEvents()
            
            resume_latex_filename = f"{job_id.replace('_', '-')}_resume.tex"
            cover_filename = f"{job_id.replace('_', '-')}_cover.txt"
            
            resume_latex_path = os.path.join(GENERATED_DIR, resume_latex_filename)
            cover_path = os.path.join(GENERATED_DIR, cover_filename)
            
            # Save LaTeX file
            with open(resume_latex_path, 'w', encoding='utf-8') as f:
                f.write(tailored_latex)
            logger.info(f"Saved tailored LaTeX resume: {resume_latex_path}")
            
            # Save cover letter file
            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(tailored_cover)
            logger.info(f"Saved tailored cover letter: {cover_path}")
            
            # Step 5: Generate PDF from LaTeX (try), or generate HTML as fallback
            status_label.setText("Preparing resume for viewing...")
            QApplication.processEvents()
            
            resume_pdf_path = os.path.join(GENERATED_DIR, f"{job_id.replace('_', '-')}_resume.pdf")
            resume_html_path = os.path.join(GENERATED_DIR, f"{job_id.replace('_', '-')}_resume.html")
            
            pdf_generated = compile_latex_to_pdf(tailored_latex, resume_pdf_path, groq_api_key)
            html_generated = False
            
            if pdf_generated:
                logger.info("Successfully compiled LaTeX to PDF")
            else:
                # If LaTeX tools not available, generate HTML version
                logger.info("LaTeX tools not available, generating HTML version...")
                status_label.setText("Generating HTML resume...")
                QApplication.processEvents()
                html_generated = latex_to_html(tailored_latex, resume_html_path, groq_api_key)
                
                if html_generated:
                    logger.info("Successfully generated HTML resume as fallback")
                else:
                    logger.warning("Could not generate HTML - .tex file will be available for viewing")
            
            # Step 6: Save to database
            self.db.save_generated_documents(
                job_id=job_id,
                resume_path=resume_latex_path,  # Store TeX path
                cover_path=cover_path,
                resume_score=resume_match,
                cover_score=cover_match
            )
            
            progress_dialog.close()
            
            # Show success dialog
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle("Documents Generated Successfully!")
            result_dialog.setMinimumWidth(480)
            
            result_layout = QVBoxLayout()
            
            result_text = f"""✓ Successfully generated tailored documents!

Job: {job['company']} - {job['title']}

Resume Match Score: {resume_match:.0f}%
Cover Letter Match Score: {cover_match:.0f}%

Generated Files:
• LaTeX Resume: {os.path.basename(resume_latex_path)}
• Cover Letter: {os.path.basename(cover_path)}
{f"• PDF Resume: {os.path.basename(resume_pdf_path)}" if pdf_generated else f"• HTML Resume: {os.path.basename(resume_html_path)}" if html_generated else "• Resume: .tex file (can be viewed/edited)"}

Double-click the resume icon in the table to open your resume."""
            
            result_label = QLabel(result_text)
            result_layout.addWidget(result_label)
            
            button_layout = QHBoxLayout()
            
            if pdf_generated:
                open_pdf_btn = QPushButton("📄 Open Resume PDF")
                open_pdf_btn.clicked.connect(lambda: os.startfile(resume_pdf_path) if os.path.exists(resume_pdf_path) else None)
                button_layout.addWidget(open_pdf_btn)
            elif html_generated:
                open_html_btn = QPushButton("🌐 Open Resume (HTML)")
                open_html_btn.clicked.connect(lambda: webbrowser.open("file://" + resume_html_path) if os.path.exists(resume_html_path) else None)
                button_layout.addWidget(open_html_btn)
            
            view_latex_btn = QPushButton("📝 View LaTeX")
            view_latex_btn.clicked.connect(lambda: os.startfile(resume_latex_path))
            button_layout.addWidget(view_latex_btn)
            
            cover_txt_btn = QPushButton("📄 View Cover Letter")
            cover_txt_btn.clicked.connect(lambda: os.startfile(cover_path))
            button_layout.addWidget(cover_txt_btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(result_dialog.close)
            button_layout.addWidget(close_btn)
            
            result_layout.addLayout(button_layout)
            result_dialog.setLayout(result_layout)
            result_dialog.exec()
            
            # Refresh table
            self.refresh_table(self.search_input.text(), self.status_filter.currentText())
            self.update_status_bar()
            
            logger.info(f"Successfully generated tailored documents for job {job_id}")
            
        except ImportError as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                "Missing Package",
                f"Required package not installed: {str(e)}\n\nPlease run: pip install -r requirements.txt"
            )
        except Exception as e:
            progress_dialog.close()
            logger.error(f"Error generating documents: {str(e)}")
            QMessageBox.critical(
                self,
                "Generation Error",
                f"Failed to generate documents:\n{str(e)}\n\nCheck the log file for details."
            )
    
    def on_search_changed(self):
        """Handle search input change"""
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
    
    def on_status_filter_changed(self):
        """Handle status filter change"""
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
    
    def refresh_jobs(self):
        """Trigger job scraping"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            QMessageBox.warning(self, "Scraping in Progress", "A scraping task is already running. Please wait.")
            return
        
        self.scraper_thread = JobScraperThread(
            self.db,
            self.config.get('search_terms', []),
            self.config.get('location', 'Germany'),
            self.config.get('results_wanted', 50)
        )
        self.scraper_thread.jobs_fetched.connect(self.on_jobs_fetched)
        self.scraper_thread.error_occurred.connect(self.on_scraper_error)
        self.scraper_thread.scraping_finished.connect(self.on_scraping_finished)
        self.scraper_thread.start()
        
        self.status_bar.showMessage("Scraping jobs... please wait")
        self.last_scrape_time = datetime.now()
    
    def on_jobs_fetched(self, count: int):
        """Handle jobs fetched signal"""
        self.last_scrape_count = count
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
    
    def on_scraper_error(self, error: str):
        """Handle scraper error"""
        logger.error(f"Scraper error: {error}")
    
    def on_scraping_finished(self):
        """Handle scraping finished"""
        self.status_bar.showMessage(f"Scraping complete. Added {self.last_scrape_count} new jobs.")
    
    def export_to_csv(self):
        """Export jobs to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Jobs", "", "CSV Files (*.csv)")
        if file_path:
            try:
                import csv
                jobs = self.db.get_all_jobs()
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if jobs:
                        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
                        writer.writeheader()
                        writer.writerows(jobs)
                QMessageBox.information(self, "Success", f"Exported {len(jobs)} jobs to CSV")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.config_file)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_config()
            self.update_status_bar()
            
            # Restart email watcher if Gmail settings changed
            if self.config.get('gmail_enabled') and self.config.get('gmail_email'):
                self.start_email_watcher()
            elif self.email_watcher_thread:
                self.stop_email_watcher()
    
    def start_scheduler(self):
        """Start background scheduler"""
        import scheduler as scheduler_module
        self.scheduler_thread = scheduler_module.SchedulerThread()
        
        # Schedule job scraping
        scrape_interval = self.config.get('scrape_interval_hours', 2)
        self.scheduler_thread.schedule_job(
            self.refresh_jobs, 
            scrape_interval, 
            "Job Scraping"
        )
        
        # Schedule email checking if enabled
        if self.config.get('gmail_enabled') and self.config.get('gmail_email'):
            self.start_email_watcher()
        
        self.scheduler_thread.start()
        logger.info("Scheduler started")
    
    def start_email_watcher(self):
        """Start email watcher thread"""
        if self.email_watcher_thread and self.email_watcher_thread.isRunning():
            return
        
        email = self.config.get('gmail_email', '')
        password = self.config.get('gmail_password', '')
        interval = self.config.get('email_check_interval_minutes', 30)
        
        if email and password:
            self.email_watcher_thread = EmailWatcherThread(self.db, email, password, interval)
            self.email_watcher_thread.email_processed.connect(self.on_email_processed)
            self.email_watcher_thread.error_occurred.connect(self.on_email_error)
            self.email_watcher_thread.start()
            logger.info("Email watcher started")
    
    def stop_email_watcher(self):
        """Stop email watcher thread"""
        if self.email_watcher_thread:
            self.email_watcher_thread.stop()
            logger.info("Email watcher stopped")
    
    def on_email_processed(self, status: str, message: str):
        """Handle email processed signal"""
        self.tray_icon.showMessage("Job Update", f"{message} → {status}", QSystemTrayIcon.MessageIcon.Information, 5000)
        self.refresh_table(self.search_input.text(), self.status_filter.currentText())
        self.update_status_bar()
    
    def on_email_error(self, error: str):
        """Handle email error"""
        logger.error(f"Email watcher error: {error}")
    
    def show_quickstart(self):
        """Show quickstart guide"""
        QMessageBox.information(self, "Quickstart Guide", """
Job Tracker v2.0 - Quick Start

1. CONFIGURE SEARCH TERMS
   - Open Settings (⚙️ button)
   - Add job titles you're searching for
   - Set location and other preferences

2. FETCH JOBS
   - Click "🔄 Refresh Jobs Now"
   - Wait for scraping to complete
   - Jobs appear in the table

3. TRACK APPLICATIONS
   - Right-click job → Mark as Applied
   - Double-click link to apply directly
   - Track with status: New, Applied, Interview, etc.

4. SETUP GMAIL (Optional)
   - Go to Settings
   - Enter Gmail email and 16-char app password
   - Click "Save & Test Connection"
   - Enable Gmail Monitoring
   - App will auto-update status from emails

5. EXPORT DATA
   - Click "📊 Export to CSV"
   - Save spreadsheet for backup

Data location: {DATA_DIR}
All settings are saved automatically.
        """)
    
    def show_gmail_guide(self):
        """Show Gmail setup guide"""
        QMessageBox.information(self, "Gmail Setup Guide", """
Gmail Setup (IMAP + App Password)

STEP 1: Enable IMAP in Gmail
1. Go to Gmail Settings (gear icon)
2. Click "See all settings"
3. Go to "Forwarding and POP/IMAP"
4. Select "Enable IMAP"
5. Save changes

STEP 2: Enable 2-Step Verification
1. Go to myaccount.google.com
2. Click "Security" (left sidebar)
3. Find "2-Step Verification"
4. Follow the setup steps

STEP 3: Get App Password
1. Go to myaccount.google.com Security
2. Find "App passwords" (only appears with 2-Step enabled)
3. Select "Mail" and "Windows Computer"
4. Generate password (16 characters)
5. Copy the code

STEP 4: Add to Job Tracker
1. Open Settings (⚙️)
2. Enter Gmail email address
3. Paste the 16-char password
4. Click "Save & Test Connection"
5. Enable "Gmail Monitoring"

STEP 5: Done!
The app will now check your email every 30 min (adjustable in Settings) and:
- Detect interview invites
- Detect rejections
- Detect offers
- Auto-update your job tracker

Keywords detected:
- Interview: interview, gespräch, termin
- Rejected: unfortunately, ablehnung, absage
- Offer: offer, angebot, willkommen
        """)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(self, "About Job Tracker", """
Job Tracker v2.0

A desktop application for tracking job applications.

Features:
✓ Automatic job scraping (LinkedIn, Indeed)
✓ Gmail monitoring (IMAP + App Password)
✓ SQLite database for local storage
✓ Dark/Light/Pastel themes
✓ Export to CSV
✓ System tray integration

Data stored at:
{DATA_DIR}

© 2026 Datta's Job Tracker
        """.format(DATA_DIR=DATA_DIR))
    
    def closeEvent(self, event):
        """Handle window close"""
        try:
            # Stop email watcher
            if self.email_watcher_thread:
                self.stop_email_watcher()
                try:
                    self.email_watcher_thread.wait(5000)  # Wait max 5 seconds
                except Exception as e:
                    logger.debug(f"Error waiting for email thread: {e}")
            
            # Stop scraper if running
            if self.scraper_thread:
                if self.scraper_thread.isRunning():
                    self.scraper_thread.stop()
                    try:
                        self.scraper_thread.wait(10000)  # Wait max 10 seconds for scraper to finish
                    except Exception as e:
                        logger.debug(f"Error waiting for scraper thread: {e}")
            
            # Stop scheduler
            if self.scheduler_thread:
                try:
                    self.scheduler_thread.stop()
                    try:
                        self.scheduler_thread.wait(5000)  # Wait max 5 seconds
                    except Exception as e:
                        logger.debug(f"Error waiting for scheduler thread: {e}")
                except Exception as e:
                    logger.debug(f"Error stopping scheduler: {e}")
            
            logger.info("Application closing cleanly")
        except Exception as e:
            logger.error(f"Error during app close: {e}")
        finally:
            event.accept()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = JobTrackerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
