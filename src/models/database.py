"""Database models and encryption utilities."""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from cryptography.fernet import Fernet
from src.config import config, DB_DIR

logger = logging.getLogger(__name__)

Base = declarative_base()


class EncryptedType:
    """Custom SQLAlchemy type for encrypted fields."""
    
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, value: str) -> bytes:
        """Encrypt a string value."""
        if value is None:
            return None
        return self.cipher.encrypt(value.encode())
    
    def decrypt(self, value: bytes) -> str:
        """Decrypt a bytes value."""
        if value is None:
            return None
        return self.cipher.decrypt(value).decode()


class Candidate(Base):
    """Candidate model for storing resume information."""
    
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    email_id = Column(String(255), unique=True, nullable=False)  # Outlook message ID
    email_date = Column(DateTime, nullable=False)
    sender_email = Column(String(255))
    sender_name = Column(String(255))
    subject = Column(Text)
    
    # Candidate information (encrypted)
    candidate_name = Column(LargeBinary)  # Encrypted
    candidate_email = Column(LargeBinary)  # Encrypted
    candidate_phone = Column(LargeBinary)  # Encrypted
    
    # Resume data
    resume_filename = Column(String(255))
    resume_hash = Column(String(64), unique=True)  # SHA-256 hash for deduplication
    resume_text = Column(LargeBinary)  # Encrypted full text
    resume_size_bytes = Column(Integer)
    
    # Extracted information (stored as encrypted JSON)
    skills = Column(LargeBinary)  # Encrypted JSON array
    education = Column(LargeBinary)  # Encrypted JSON array
    experience = Column(LargeBinary)  # Encrypted JSON array
    
    # Comprehensive report fields (encrypted)
    executive_summary = Column(LargeBinary)  # Encrypted executive summary
    experience_highlights = Column(LargeBinary)  # Encrypted JSON array
    education_highlights = Column(LargeBinary)  # Encrypted JSON array
    interesting_facts = Column(LargeBinary)  # Encrypted JSON array
    
    # Scoring
    score = Column(Float, default=0.0)
    score_breakdown = Column(LargeBinary)  # Encrypted JSON with detailed scoring
    
    # Status and metadata
    status = Column(String(50), default='new')  # new, interested, pass
    tags = Column(Text)  # Comma-separated tags
    notes = Column(LargeBinary)  # Encrypted notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Processing flags
    is_parsed = Column(Boolean, default=False)
    is_scored = Column(Boolean, default=False)
    parse_error = Column(Text)
    
    def to_dict(self, cipher: EncryptedType) -> Dict[str, Any]:
        """Convert to dictionary with decrypted values."""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'sender_email': self.sender_email,
            'sender_name': self.sender_name,
            'subject': self.subject,
            'candidate_name': cipher.decrypt(self.candidate_name) if self.candidate_name else None,
            'candidate_email': cipher.decrypt(self.candidate_email) if self.candidate_email else None,
            'candidate_phone': cipher.decrypt(self.candidate_phone) if self.candidate_phone else None,
            'resume_filename': self.resume_filename,
            'resume_size_bytes': self.resume_size_bytes,
            'skills': json.loads(cipher.decrypt(self.skills)) if self.skills else [],
            'education': json.loads(cipher.decrypt(self.education)) if self.education else [],
            'experience': json.loads(cipher.decrypt(self.experience)) if self.experience else [],
            'executive_summary': cipher.decrypt(self.executive_summary) if self.executive_summary else None,
            'experience_highlights': json.loads(cipher.decrypt(self.experience_highlights)) if self.experience_highlights else [],
            'education_highlights': json.loads(cipher.decrypt(self.education_highlights)) if self.education_highlights else [],
            'interesting_facts': json.loads(cipher.decrypt(self.interesting_facts)) if self.interesting_facts else [],
            'score': self.score,
            'score_breakdown': json.loads(cipher.decrypt(self.score_breakdown)) if self.score_breakdown else {},
            'status': self.status,
            'tags': self.tags.split(',') if self.tags else [],
            'notes': cipher.decrypt(self.notes) if self.notes else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_parsed': self.is_parsed,
            'is_scored': self.is_scored,
            'parse_error': self.parse_error
        }


class ProcessingLog(Base):
    """Log table for tracking email processing."""
    
    __tablename__ = 'processing_logs'
    
    id = Column(Integer, primary_key=True)
    email_id = Column(String(255))
    action = Column(String(50))  # fetch, parse, score, error
    status = Column(String(50))  # success, failed, skipped
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    """Database manager with encryption support."""
    
    def __init__(self):
        self.db_path = DB_DIR / config.get_setting('database.path', 'cvlens.db')
        self.engine = None
        self.SessionLocal = None
        self.cipher = EncryptedType(config.aes_key)
        self._init_db()
    
    def _init_db(self):
        """Initialize database connection and create tables."""
        try:
            # Create engine with SQLite
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=config.debug_mode
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def add_candidate(self, session: Session, candidate_data: Dict[str, Any]) -> Candidate:
        """Add a new candidate to the database."""
        try:
            # Encrypt sensitive fields
            candidate = Candidate(
                email_id=candidate_data['email_id'],
                email_date=candidate_data['email_date'],
                sender_email=candidate_data.get('sender_email'),
                sender_name=candidate_data.get('sender_name'),
                subject=candidate_data.get('subject'),
                resume_filename=candidate_data.get('resume_filename'),
                resume_hash=candidate_data.get('resume_hash'),
                resume_size_bytes=candidate_data.get('resume_size_bytes')
            )
            
            # Encrypt sensitive data
            if candidate_data.get('candidate_name'):
                candidate.candidate_name = self.cipher.encrypt(candidate_data['candidate_name'])
            if candidate_data.get('candidate_email'):
                candidate.candidate_email = self.cipher.encrypt(candidate_data['candidate_email'])
            if candidate_data.get('candidate_phone'):
                candidate.candidate_phone = self.cipher.encrypt(candidate_data['candidate_phone'])
            if candidate_data.get('resume_text'):
                candidate.resume_text = self.cipher.encrypt(candidate_data['resume_text'])
            
            # Encrypt JSON fields
            for field in ['skills', 'education', 'experience', 'score_breakdown']:
                if candidate_data.get(field):
                    setattr(candidate, field, self.cipher.encrypt(
                        json.dumps(candidate_data[field])
                    ))
            
            session.add(candidate)
            session.commit()
            session.refresh(candidate)
            
            return candidate
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding candidate: {str(e)}")
            raise
    
    def get_candidate_by_hash(self, session: Session, resume_hash: str) -> Optional[Candidate]:
        """Get candidate by resume hash."""
        return session.query(Candidate).filter_by(resume_hash=resume_hash).first()
    
    def get_candidate_by_email_id(self, session: Session, email_id: str) -> Optional[Candidate]:
        """Get candidate by email ID."""
        return session.query(Candidate).filter_by(email_id=email_id).first()
    
    def update_candidate_status(self, session: Session, candidate_id: int, status: str, notes: str = None):
        """Update candidate status."""
        try:
            candidate = session.query(Candidate).filter_by(id=candidate_id).first()
            if candidate:
                candidate.status = status
                if notes:
                    candidate.notes = self.cipher.encrypt(notes)
                candidate.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating candidate status: {str(e)}")
            return False
    
    def log_processing(self, session: Session, email_id: str, action: str, status: str, message: str = None):
        """Log processing action."""
        try:
            log_entry = ProcessingLog(
                email_id=email_id,
                action=action,
                status=status,
                message=message
            )
            session.add(log_entry)
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging processing: {str(e)}")
    
    def purge_all_data(self):
        """Purge all data from the database."""
        try:
            with self.get_session() as session:
                session.query(Candidate).delete()
                session.query(ProcessingLog).delete()
                session.commit()
                logger.info("All data purged from database")
                return True
                
        except Exception as e:
            logger.error(f"Error purging data: {str(e)}")
            return False


# Global database instance
db = Database() 