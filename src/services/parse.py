"""Document parsing service for extracting information from resumes."""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import openai
from src.config import config
from src.models.file_storage import file_storage

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing resume documents."""
    
    def __init__(self):
        # Configure OpenAI
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("OpenAI client initialized for resume analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        
    def parse_all_pending(self) -> Tuple[int, int]:
        """
        Parse all pending resumes from markdown files.
        
        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0
        
        # Get all candidates
        candidates = file_storage.list_all_candidates()
        
        # Filter unparsed candidates
        unparsed_candidates = [c for c in candidates if not c.is_parsed]
        
        for candidate in unparsed_candidates:
            try:
                # Get file path
                candidate_dir = file_storage.get_candidate_dir(candidate.email_id)
                file_path = candidate_dir / "attachments" / candidate.resume_filename
                
                if not file_path.exists():
                    logger.error(f"Resume file not found: {file_path}")
                    candidate.parse_error = "File not found"
                    candidate.updated_at = datetime.utcnow()
                    file_storage.save_candidate_metadata(candidate)
                    error_count += 1
                    continue
                
                # Parse resume
                parsed_data = self.parse_resume(file_path, candidate.email_id)
                
                # Update candidate with parsed data
                self._update_candidate_with_parsed_data(candidate, parsed_data)
                
                success_count += 1
                logger.info(f"Successfully parsed: {candidate.resume_filename}")
                
            except Exception as e:
                logger.error(f"Error parsing resume {candidate.resume_filename}: {str(e)}")
                candidate.parse_error = str(e)
                candidate.updated_at = datetime.utcnow()
                file_storage.save_candidate_metadata(candidate)
                error_count += 1
                
                file_storage.log_processing(
                    candidate.email_id,
                    'parse',
                    'failed',
                    str(e)
                )
        
        logger.info(f"Parsing completed: {success_count} success, {error_count} errors")
        return success_count, error_count
    
    def parse_resume(self, file_path: Path, email_id: str = None) -> Dict[str, Any]:
        """Parse a single resume file using OpenAI."""
        file_ext = file_path.suffix.lower()
        
        # Only support PDF files
        if file_ext != '.pdf':
            raise ValueError(f"Unsupported file type: {file_ext}. Only PDF files are supported.")
        
        # Process with OpenAI
        summary_text = self._analyze_pdf_with_openai(file_path, email_id)
        
        # Return simple parsed data structure
        parsed_data = {
            'text': summary_text,
            'name': f"Candidate from {file_path.name}",
            'email': email_id or "unknown@email.com",
            'phone': "See summary",
            'skills': ["See summary for skills"],
            'education': [{'text': "See summary for education"}],
            'experience': [{'title': "See summary", 'years': 0}],
            'executive_summary': summary_text[:500] + "..." if len(summary_text) > 500 else summary_text,
            'experience_highlights': ["See full summary"],
            'education_highlights': ["See full summary"],
            'interesting_facts': ["See full summary"],
            'strengths': ["See full summary"],
            'weaknesses': ["See full summary"],
            'certifications': ["See full summary"],
            'full_summary': summary_text
        }
        
        logger.info(f"Parsed data for {file_path.name}:")
        logger.info(f"  - Summary length: {len(summary_text)} characters")
        
        return parsed_data
    
    def _analyze_pdf_with_openai(self, file_path: Path, email_id: str = None) -> str:
        """Analyze PDF using OpenAI's simple file upload approach."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized - API key required for PDF processing")
        
        try:
            logger.info(f"Processing PDF with OpenAI: {file_path.name}")
            
            # Step 1: Archive PDF to data/resumes folder
            resumes_dir = Path("data/resumes")
            resumes_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if email_id:
                archived_filename = f"{timestamp}_{email_id}_{file_path.name}"
            else:
                archived_filename = f"{timestamp}_{file_path.name}"
            archived_path = resumes_dir / archived_filename
            
            # Copy the PDF to the resumes folder
            shutil.copy2(file_path, archived_path)
            logger.info(f"PDF archived to: {archived_path}")
            
            # Step 2: Upload PDF to OpenAI
            with open(file_path, 'rb') as pdf_file:
                file = self.openai_client.files.create(
                    file=pdf_file,
                    purpose="user_data"
                )
            
            logger.info(f"PDF uploaded with file ID: {file.id}")
            
            # Step 3: Analyze with OpenAI
            response = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "file_id": file.id,
                            },
                            {
                                "type": "input_text",
                                "text": "Please summarize this resume or document. Provide a comprehensive summary including the person's background, experience, skills, education, and any other relevant information.",
                            },
                        ]
                    }
                ]
            )
            
            # Get the response text
            summary_text = response.output[0].content[0].text
            
            # Print to terminal
            print("\n" + "="*80)
            print(f"RESUME SUMMARY FOR: {file_path.name}")
            print(f"ARCHIVED AS: {archived_filename}")
            print("="*80)
            print(summary_text)
            print("="*80 + "\n")
            
            # Clean up uploaded file
            try:
                self.openai_client.files.delete(file.id)
                logger.info(f"Cleaned up uploaded file: {file.id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded file {file.id}: {cleanup_error}")
            
            return summary_text
            
        except Exception as e:
            logger.error(f"PDF processing failed for {file_path.name}: {str(e)}")
            raise
    
    def _update_candidate_with_parsed_data(self, candidate, parsed_data: Dict[str, Any]):
        """Update candidate record with parsed data."""
        
        # Update basic info
        if parsed_data.get('name'):
            candidate.candidate_name = parsed_data['name']
        if parsed_data.get('email'):
            candidate.candidate_email = parsed_data['email']
        if parsed_data.get('phone'):
            candidate.candidate_phone = parsed_data['phone']
        
        # Update extracted data
        if parsed_data.get('skills'):
            candidate.skills = parsed_data['skills']
        if parsed_data.get('education'):
            candidate.education = parsed_data['education']
        if parsed_data.get('experience'):
            candidate.experience = parsed_data['experience']
        
        # Update summary fields
        if parsed_data.get('executive_summary'):
            candidate.executive_summary = parsed_data['executive_summary']
        if parsed_data.get('full_summary'):
            candidate.interesting_facts = [parsed_data['full_summary']]
        
        # Update flags
        candidate.is_parsed = True
        candidate.processed_at = datetime.utcnow()
        candidate.updated_at = datetime.utcnow()
        
        # Save updated metadata
        file_storage.save_candidate_metadata(candidate)
        
        # Save detailed resume analysis
        file_storage.save_resume_analysis(candidate.email_id, parsed_data)
        
        # Log success
        file_storage.log_processing(
            candidate.email_id,
            'parse',
            'success',
            f'Generated summary with {len(parsed_data.get("full_summary", ""))} characters'
        )

# Global parser instance
resume_parser = ResumeParser() 