"""Document parsing service for extracting information from resumes."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import openai
import base64
import os
from src.config import config, CACHE_DIR
from src.models.file_storage import file_storage
from src.models.candidate import CandidateData
from src.services.prompts import COMPREHENSIVE_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class ResumeParser:
    """Service for parsing resume documents."""
    
    def __init__(self):
        # Configure OpenAI
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("OpenAI client initialized for comprehensive resume analysis")
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
                parsed_data = self.parse_resume(file_path)
                
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
    
    def parse_resume(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single resume file and generate comprehensive report."""
        file_ext = file_path.suffix.lower()
        
        # Only support PDF files
        if file_ext == '.pdf':
            report = self._generate_comprehensive_report(file_path=file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}. Only PDF files are supported.")
        
        # Convert report to expected format for database
        parsed_data = {
            'text': report.get('raw_text', ''),
            'name': report.get('personal_info', {}).get('name'),
            'email': report.get('personal_info', {}).get('email'),
            'phone': report.get('personal_info', {}).get('phone'),
            'skills': report.get('key_skills', []),
            'education': [{'text': edu} for edu in report.get('education_highlights', [])],
            'experience': [{'title': exp, 'years': 0} for exp in report.get('experience_highlights', [])],
            'executive_summary': report.get('executive_summary', ''),
            'experience_highlights': report.get('experience_highlights', []),
            'education_highlights': report.get('education_highlights', []),
            'interesting_facts': report.get('interesting_facts', [])
        }
        
        # Debug logging
        logger.info(f"Parsed data for {file_path.name}:")
        logger.info(f"  - Name: {parsed_data.get('name')}")
        logger.info(f"  - Email: {parsed_data.get('email')}")
        logger.info(f"  - Skills count: {len(parsed_data.get('skills', []))}")
        logger.info(f"  - Executive summary length: {len(parsed_data.get('executive_summary', ''))}")
        logger.info(f"  - Experience highlights count: {len(parsed_data.get('experience_highlights', []))}")
        logger.info(f"  - Education highlights count: {len(parsed_data.get('education_highlights', []))}")
        logger.info(f"  - Interesting facts count: {len(parsed_data.get('interesting_facts', []))}")
        
        return parsed_data
    
  

    

    
    def _generate_comprehensive_report(self, file_path: Path) -> Dict[str, Any]:
        """Generate comprehensive candidate report from PDF using OpenAI files API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError("Only PDF files are supported")
        
        try:
            # Upload PDF file to OpenAI
            with open(file_path, 'rb') as f:
                file_obj = self.openai_client.files.create(
                    file=f,
                    purpose="user_data"
                )
            
            # Generate comprehensive report using files API
            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "file_id": file_obj.id,
                            },
                            {
                                "type": "input_text",
                                "text": COMPREHENSIVE_ANALYSIS_PROMPT,
                            },
                        ]
                    }
                ]
            )
            
            # Clean up uploaded file
            try:
                self.openai_client.files.delete(file_obj.id)
            except:
                pass  # Don't fail if cleanup fails
            
            # Parse the JSON response
            import json
            try:
                report_data = json.loads(response.output_text)
                logger.info(f"Successfully generated PDF report: {file_path.name}")
                logger.info(f"OpenAI report keys: {list(report_data.keys())}")
                return report_data
            except json.JSONDecodeError:
                # Fallback: treat as raw text
                logger.warning(f"OpenAI response was not valid JSON, using raw text: {file_path.name}")
                logger.warning(f"Raw response: {response.output_text[:500]}...")
                return {
                    "personal_info": {"name": None, "email": None, "phone": None},
                    "executive_summary": "",
                    "experience_highlights": [],
                    "education_highlights": [],
                    "key_skills": [],
                    "interesting_facts": [],
                    "raw_text": response.output_text
                }
            
        except Exception as e:
            logger.error(f"PDF report generation failed for {file_path.name}: {str(e)}")
            raise e
    

    
    def _update_candidate_with_parsed_data(self, candidate: CandidateData, parsed_data: Dict[str, Any]):
        """Update candidate record with parsed data."""
        
        # Update basic info (no encryption needed for local files)
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
        
        # Update new fields
        if parsed_data.get('executive_summary'):
            candidate.executive_summary = parsed_data['executive_summary']
        if parsed_data.get('interesting_facts'):
            candidate.interesting_facts = parsed_data['interesting_facts']
        if parsed_data.get('experience_highlights'):
            candidate.experience_highlights = parsed_data['experience_highlights']
        if parsed_data.get('education_highlights'):
            candidate.education_highlights = parsed_data['education_highlights']
        
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
            f'Generated comprehensive report with {len(parsed_data.get("skills", []))} skills'
        )


# Global parser instance
resume_parser = ResumeParser() 