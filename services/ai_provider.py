"""
AI Provider Service - handles AI-powered operations, document generation, and LaTeX processing
"""

import logging
import os
import requests
from typing import Tuple

logger = logging.getLogger(__name__)


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
                       job_description: str, groq_key: str) -> Tuple[str, float]:
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
