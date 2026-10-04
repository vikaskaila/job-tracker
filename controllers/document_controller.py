"""
Document Controller - handles resume and cover letter generation
"""

import logging
import os
from typing import Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal
from models.database import GENERATED_DIR

# Import AI provider functions
from services.ai_provider import (
    fetch_job_description_from_url, extract_cover_letter_from_docx,
    read_latex_template, tailor_latex_resume, compile_latex_to_pdf,
    latex_to_html
)

logger = logging.getLogger(__name__)


class DocumentGeneratorThread(QThread):
    """Background thread for generating tailored documents"""
    progress_updated = pyqtSignal(str)  # Progress message
    document_generated = pyqtSignal(str, str, float, float)  # resume_path, cover_path, resume_score, cover_score
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, job_id: str, job: dict, base_resume_path: str, base_cover_path: str, groq_key: str, db=None):
        super().__init__()
        self.job_id = job_id
        self.job = job
        self.base_resume_path = base_resume_path
        self.base_cover_path = base_cover_path
        self.groq_key = groq_key
        self.db = db
    
    def run(self):
        """Generate tailored documents"""
        try:
            # Step 1: Read base files
            self.progress_updated.emit("Reading base resume template...")
            base_latex = read_latex_template(self.base_resume_path)
            if not base_latex:
                raise Exception("LaTeX template is empty")
            
            self.progress_updated.emit("Reading cover letter template...")
            base_cover = extract_cover_letter_from_docx(self.base_cover_path)
            if not base_cover:
                raise Exception("Cover letter template is empty")
            
            # Step 2: Fetch job description
            self.progress_updated.emit("Fetching job description...")
            job_desc = self.job.get('description_snippet', '')
            
            if not job_desc or len(job_desc.strip()) < 100:
                job_desc = fetch_job_description_from_url(
                    self.job.get('apply_link', ''),
                    self.groq_key
                ) or f"Position: {self.job['title']} at {self.job['company']}"
            
            # Step 3: Generate tailored resume
            self.progress_updated.emit("Tailoring resume with AI...")
            tailored_latex, resume_score = tailor_latex_resume(
                base_latex,
                self.job['title'],
                self.job['company'],
                job_desc,
                self.groq_key
            )
            
            if not tailored_latex:
                raise Exception("Failed to generate tailored resume")
            
            # Step 4: Generate tailored cover letter
            self.progress_updated.emit("Tailoring cover letter with AI...")
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            
            cover_prompt = f"""Write a compelling cover letter for this job.

JOB DETAILS:
Title: {self.job['title']}
Company: {self.job['company']}
Location: {self.job.get('location', 'Unknown')}
Description: {job_desc[:1500]}

RETURN: Plain text, professional cover letter"""
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": cover_prompt}],
                max_tokens=1500
            )
            
            tailored_cover = response.choices[0].message.content.strip()
            
            # Calculate cover score
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                
                vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
                vectors = vectorizer.fit_transform([job_desc.lower(), tailored_cover.lower()])
                cover_score = float(cosine_similarity(vectors[0:1], vectors[1:2])[0][0] * 100)
            except:
                cover_score = 75.0
            
            # Step 5: Save files
            self.progress_updated.emit("Saving documents...")
            resume_path = os.path.join(GENERATED_DIR, f"{self.job_id}_resume.tex")
            cover_path = os.path.join(GENERATED_DIR, f"{self.job_id}_cover.txt")
            pdf_path = os.path.join(GENERATED_DIR, f"{self.job_id}_resume.pdf")
            
            # Save LaTeX
            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(tailored_latex)
            
            # Save cover letter
            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(tailored_cover)
            
            # Try to generate PDF
            self.progress_updated.emit("Generating PDF from LaTeX...")
            compile_latex_to_pdf(tailored_latex, pdf_path, self.groq_key)
            
            logger.info(f"Generated documents for job {self.job_id}")
            self.document_generated.emit(resume_path, cover_path, resume_score, cover_score)
        
        except Exception as e:
            logger.error(f"Error generating documents: {e}")
            self.error_occurred.emit(str(e))


class DocumentController:
    """Controller for document generation"""
    
    def __init__(self, db):
        """Initialize with database"""
        self.db = db
        self.generator_thread = None
    
    def generate_documents(self, job_id: str, base_resume_path: str, base_cover_path: str,
                          groq_key: str) -> DocumentGeneratorThread:
        """Generate tailored documents for a job"""
        job = self.db.get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        self.generator_thread = DocumentGeneratorThread(
            job_id, job, base_resume_path, base_cover_path, groq_key, self.db
        )
        return self.generator_thread
    
    def save_documents(self, job_id: str, resume_path: str, cover_path: str,
                       resume_score: float, cover_score: float) -> bool:
        """Save generated document paths and scores to database"""
        return self.db.save_generated_documents(
            job_id=job_id,
            resume_path=resume_path,
            cover_path=cover_path,
            resume_score=resume_score,
            cover_score=cover_score
        )
