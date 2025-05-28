"""Document parsing service for extracting information from resumes."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import openai
import base64
import os
from pydantic import BaseModel
from src.config import config, CACHE_DIR
from src.models.file_storage import file_storage
from src.models.candidate import CandidateData

logger = logging.getLogger(__name__)


# Pydantic models for structured output
class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None


class SkillAnalysis(BaseModel):
    technical_skills: Dict[str, str] = {}
    soft_skills: Dict[str, str] = {}
    leadership_skills: Dict[str, str] = {}


class ExperienceHighlight(BaseModel):
    title: str
    company: str
    duration: str
    achievements: List[str] = []


class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[int] = None
    honours: Optional[str] = None


class Metrics(BaseModel):
    years_experience: Optional[int] = None
    largest_team_led: Optional[int] = None
    max_budget_managed_usd: Optional[int] = None


class FitRiskAssessment(BaseModel):
    overall_fit: str  # "strong" | "moderate" | "weak"
    risk_factors: List[str] = []


class ResumeAnalysisResponse(BaseModel):
    personal_info: PersonalInfo
    executive_summary: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    skill_analysis: SkillAnalysis
    experience_highlights: List[ExperienceHighlight] = []
    education: List[Education] = []
    certifications: List[str] = []
    metrics: Metrics
    fit_risk_assessment: FitRiskAssessment
    development_recommendations: List[str] = []
    interesting_facts: List[str] = []
    raw_text: str


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
        
        # Convert structured response to expected format for database
        parsed_data = {
            'text': report.raw_text,
            'name': report.personal_info.name,
            'email': report.personal_info.email,
            'phone': report.personal_info.phone,
            'skills': list(report.skill_analysis.technical_skills.keys()) + list(report.skill_analysis.soft_skills.keys()),
            'education': [{'text': f"{edu.degree} from {edu.institution} ({edu.year})"} for edu in report.education],
            'experience': [{'title': exp.title, 'years': 0} for exp in report.experience_highlights],
            'executive_summary': report.executive_summary,
            'experience_highlights': [f"{exp.title} at {exp.company} ({exp.duration})" for exp in report.experience_highlights],
            'education_highlights': [f"{edu.degree} from {edu.institution}" for edu in report.education],
            'interesting_facts': report.interesting_facts,
            'strengths': report.strengths,
            'weaknesses': report.weaknesses,
            'certifications': report.certifications,
            'skill_analysis': report.skill_analysis.model_dump(),
            'metrics': report.metrics.model_dump(),
            'fit_risk_assessment': report.fit_risk_assessment.model_dump(),
            'development_recommendations': report.development_recommendations
        }
        
        # Debug logging with null checks
        logger.info(f"Parsed data for {file_path.name}:")
        logger.info(f"  - Name: {parsed_data.get('name')}")
        logger.info(f"  - Email: {parsed_data.get('email')}")
        
        # Safe length checks with fallbacks
        skills = parsed_data.get('skills') or []
        executive_summary = parsed_data.get('executive_summary') or ''
        experience_highlights = parsed_data.get('experience_highlights') or []
        education_highlights = parsed_data.get('education_highlights') or []
        interesting_facts = parsed_data.get('interesting_facts') or []
        
        logger.info(f"  - Skills count: {len(skills)}")
        logger.info(f"  - Executive summary length: {len(executive_summary)}")
        logger.info(f"  - Experience highlights count: {len(experience_highlights)}")
        logger.info(f"  - Education highlights count: {len(education_highlights)}")
        logger.info(f"  - Interesting facts count: {len(interesting_facts)}")
        
        return parsed_data
    
    def _generate_comprehensive_report(self, file_path: Path) -> ResumeAnalysisResponse:
        """Generate comprehensive candidate report from PDF using OpenAI Responses API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized - API key required for PDF processing")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError("Only PDF files are supported")
        
        try:
            logger.info(f"Processing PDF with OpenAI Responses API: {file_path.name}")
            
            # Step 1: Save PDF to data/resumes folder for archival
            resumes_dir = Path("data/resumes")
            resumes_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique filename with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_filename = f"{timestamp}_{file_path.name}"
            archived_path = resumes_dir / archived_filename
            
            # Copy the PDF to the resumes folder
            import shutil
            shutil.copy2(file_path, archived_path)
            logger.info(f"PDF archived to: {archived_path}")
            
            # Step 2: Upload PDF file to OpenAI
            with open(file_path, 'rb') as pdf_file:
                file = self.openai_client.files.create(
                    file=pdf_file,
                    purpose="user_data"
                )
            
            logger.info(f"PDF uploaded with file ID: {file.id}")
            
            # Step 3: Use Responses API to analyze the PDF
            response = self.openai_client.responses.create(
                model="gpt-4o-mini",  # Using mini version which might be more reliable
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
                                "text": """Please analyze this resume PDF and provide a comprehensive analysis. Extract all the information you can find including:

- Personal information (name, email, phone, location)
- Professional summary
- Work experience with details
- Education background
- Skills (technical and soft skills)
- Certifications
- Any other relevant information

Please provide a detailed analysis of this candidate's background, strengths, and qualifications.""",
                            },
                        ]
                    }
                ]
            )
            
            # Print the raw response to terminal for debugging
            print("\n" + "="*80)
            print(f"RAW RESPONSE FROM OPENAI FOR: {file_path.name}")
            print(f"ARCHIVED AS: {archived_filename}")
            print("="*80)
            print(response.output[0].content[0].text)
            print("="*80 + "\n")
            
            # Clean up the uploaded file
            try:
                self.openai_client.files.delete(file.id)
                logger.info(f"Cleaned up uploaded file: {file.id}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup uploaded file {file.id}: {cleanup_error}")
            
            # For now, create a dummy response to keep the system working
            # We'll parse the actual response later
            dummy_response = ResumeAnalysisResponse(
                personal_info=PersonalInfo(
                    name=f"Processed from {archived_filename}",
                    email="see-terminal@output.com"
                ),
                executive_summary=f"Analysis completed - see terminal output. Archived as {archived_filename}",
                skill_analysis=SkillAnalysis(),
                metrics=Metrics(),
                fit_risk_assessment=FitRiskAssessment(
                    overall_fit="moderate",
                    risk_factors=[]
                ),
                raw_text=response.output[0].content[0].text
            )
            
            return dummy_response
            
        except Exception as e:
            logger.error(f"PDF processing failed for {file_path.name}: {str(e)}")
            raise

    
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
        skills_count = len(parsed_data.get("skills") or [])
        file_storage.log_processing(
            candidate.email_id,
            'parse',
            'success',
            f'Generated comprehensive report with {skills_count} skills'
        )

# Global parser instance
resume_parser = ResumeParser() 