"""Candidate data models for markdown-based storage."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json


@dataclass
class CandidateData:
    """Data model for candidate information stored in markdown files."""
    
    # Email metadata
    email_id: str
    email_date: datetime
    sender_email: str
    sender_name: str
    subject: str
    
    # Resume metadata
    resume_filename: str
    resume_hash: str
    resume_size_bytes: int = 0
    
    # Candidate information
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    
    # Parsed resume data
    skills: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    executive_summary: str = ""
    experience_highlights: List[str] = field(default_factory=list)
    education_highlights: List[str] = field(default_factory=list)
    interesting_facts: List[str] = field(default_factory=list)
    
    # Scoring
    score: float = 0.0
    score_breakdown: Dict[str, Any] = field(default_factory=dict)
    
    # Status and decisions
    status: str = "new"  # new, interested, pass
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    # Processing flags
    is_parsed: bool = False
    is_scored: bool = False
    parse_error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'email_id': self.email_id,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'subject': self.subject,
            'resume_filename': self.resume_filename,
            'resume_hash': self.resume_hash,
            'resume_size_bytes': self.resume_size_bytes,
            'candidate_name': self.candidate_name,
            'candidate_email': self.candidate_email,
            'candidate_phone': self.candidate_phone,
            'skills': self.skills,
            'education': self.education,
            'experience': self.experience,
            'executive_summary': self.executive_summary,
            'experience_highlights': self.experience_highlights,
            'education_highlights': self.education_highlights,
            'interesting_facts': self.interesting_facts,
            'score': self.score,
            'score_breakdown': self.score_breakdown,
            'status': self.status,
            'tags': self.tags,
            'notes': self.notes,
            'is_parsed': self.is_parsed,
            'is_scored': self.is_scored,
            'parse_error': self.parse_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CandidateData':
        """Create instance from dictionary."""
        # Convert datetime strings back to datetime objects
        if data.get('email_date'):
            data['email_date'] = datetime.fromisoformat(data['email_date'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('processed_at'):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        
        return cls(**data)


@dataclass
class ProcessingLogEntry:
    """Simple processing log entry."""
    
    email_id: str
    action: str  # fetch, parse, score, error
    status: str  # success, failed, skipped
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'email_id': self.email_id,
            'action': self.action,
            'status': self.status,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingLogEntry':
        """Create instance from dictionary."""
        if data.get('timestamp'):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data) 