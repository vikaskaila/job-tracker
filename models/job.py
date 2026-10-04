"""
Job model - represents a job posting
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Job:
    """Job posting data model"""
    
    id: str
    title: str
    company: str
    apply_link: str
    location: str = ""
    posted_date: str = ""
    description_snippet: str = ""
    company_website: Optional[str] = None
    applied_date: Optional[str] = None
    status: str = "New"
    last_email_matched: Optional[str] = None
    notes: str = ""
    work_type: Optional[str] = None
    priority: int = 3
    is_favorite: int = 0
    generated_resume_path: Optional[str] = None
    generated_cover_path: Optional[str] = None
    match_score_resume: Optional[float] = None
    match_score_cover: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job instance from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> dict:
        """Convert Job instance to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'apply_link': self.apply_link,
            'location': self.location,
            'posted_date': self.posted_date,
            'description_snippet': self.description_snippet,
            'company_website': self.company_website,
            'applied_date': self.applied_date,
            'status': self.status,
            'last_email_matched': self.last_email_matched,
            'notes': self.notes,
            'work_type': self.work_type,
            'priority': self.priority,
            'is_favorite': self.is_favorite,
            'generated_resume_path': self.generated_resume_path,
            'generated_cover_path': self.generated_cover_path,
            'match_score_resume': self.match_score_resume,
            'match_score_cover': self.match_score_cover,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
