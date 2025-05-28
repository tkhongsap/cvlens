"""File storage operations for markdown-based candidate data."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from src.config import DATA_DIR
from src.models.candidate import CandidateData, ProcessingLogEntry

logger = logging.getLogger(__name__)

# Define storage paths
CANDIDATES_DIR = DATA_DIR / "candidates"
PROCESSING_LOG_FILE = DATA_DIR / "processing_log.md"
SETTINGS_DIR = DATA_DIR / "settings"
INDEX_FILE = CANDIDATES_DIR / "index.md"

# Ensure directories exist
for dir_path in [CANDIDATES_DIR, SETTINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class FileStorage:
    """File-based storage operations for candidate data."""
    
    def __init__(self):
        self.candidates_dir = CANDIDATES_DIR
        self.processing_log_file = PROCESSING_LOG_FILE
        self.index_file = INDEX_FILE
    
    def get_candidate_dir(self, email_id: str) -> Path:
        """Get the directory path for a candidate."""
        return self.candidates_dir / email_id
    
    def save_candidate_metadata(self, candidate: CandidateData) -> bool:
        """Save candidate metadata to markdown file."""
        try:
            candidate_dir = self.get_candidate_dir(candidate.email_id)
            candidate_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_file = candidate_dir / "metadata.md"
            
            # Create metadata markdown content
            content = f"""# Candidate Metadata

## Email Information
- **Email ID**: {candidate.email_id}
- **Date**: {candidate.email_date.strftime('%Y-%m-%d %H:%M:%S') if candidate.email_date else 'N/A'}
- **From**: {candidate.sender_name} <{candidate.sender_email}>
- **Subject**: {candidate.subject}

## Resume Information
- **Filename**: {candidate.resume_filename}
- **Hash**: {candidate.resume_hash}
- **Size**: {candidate.resume_size_bytes} bytes

## Candidate Details
- **Name**: {candidate.candidate_name or 'Not extracted'}
- **Email**: {candidate.candidate_email or 'Not extracted'}
- **Phone**: {candidate.candidate_phone or 'Not extracted'}

## Processing Status
- **Parsed**: {candidate.is_parsed}
- **Scored**: {candidate.is_scored}
- **Parse Error**: {candidate.parse_error or 'None'}

## Timestamps
- **Created**: {candidate.created_at.strftime('%Y-%m-%d %H:%M:%S') if candidate.created_at else 'N/A'}
- **Updated**: {candidate.updated_at.strftime('%Y-%m-%d %H:%M:%S') if candidate.updated_at else 'N/A'}
- **Processed**: {candidate.processed_at.strftime('%Y-%m-%d %H:%M:%S') if candidate.processed_at else 'N/A'}

---
<!-- JSON Data for programmatic access -->
```json
{json.dumps(candidate.to_dict(), indent=2)}
```
"""
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved metadata for candidate: {candidate.email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving candidate metadata: {str(e)}")
            return False
    
    def load_candidate_metadata(self, email_id: str) -> Optional[CandidateData]:
        """Load candidate metadata from markdown file."""
        try:
            metadata_file = self.get_candidate_dir(email_id) / "metadata.md"
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract JSON data from markdown
            json_start = content.find('```json\n') + 8
            json_end = content.find('\n```', json_start)
            
            if json_start > 7 and json_end > json_start:
                json_data = content[json_start:json_end]
                data = json.loads(json_data)
                return CandidateData.from_dict(data)
            
            logger.warning(f"No JSON data found in metadata file: {metadata_file}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading candidate metadata: {str(e)}")
            return None
    
    def save_resume_analysis(self, email_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Save resume analysis to markdown file."""
        try:
            candidate_dir = self.get_candidate_dir(email_id)
            analysis_file = candidate_dir / "resume_analysis.md"
            
            content = f"""# Resume Analysis

## Executive Summary
{analysis_data.get('executive_summary', 'No summary available.')}

## Experience Highlights
"""
            
            experience_highlights = analysis_data.get('experience_highlights', [])
            if experience_highlights:
                for i, highlight in enumerate(experience_highlights, 1):
                    content += f"{i}. {highlight}\n"
            else:
                content += "No experience highlights identified.\n"
            
            content += "\n## Education Highlights\n"
            education_highlights = analysis_data.get('education_highlights', [])
            if education_highlights:
                for i, edu in enumerate(education_highlights, 1):
                    content += f"{i}. {edu}\n"
            else:
                content += "No education highlights identified.\n"
            
            content += "\n## Key Skills\n"
            skills = analysis_data.get('skills', [])
            if skills:
                # Group skills in rows of 5
                for i in range(0, len(skills), 5):
                    skill_group = skills[i:i+5]
                    content += "• " + " • ".join(skill_group) + "\n"
            else:
                content += "No skills identified.\n"
            
            content += "\n## Interesting Facts\n"
            interesting_facts = analysis_data.get('interesting_facts', [])
            if interesting_facts:
                for i, fact in enumerate(interesting_facts, 1):
                    content += f"{i}. {fact}\n"
            else:
                content += "No interesting facts identified.\n"
            
            content += f"""
---
<!-- JSON Data for programmatic access -->
```json
{json.dumps(analysis_data, indent=2)}
```
"""
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved resume analysis for: {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving resume analysis: {str(e)}")
            return False
    
    def load_resume_analysis(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Load resume analysis from markdown file."""
        try:
            analysis_file = self.get_candidate_dir(email_id) / "resume_analysis.md"
            
            if not analysis_file.exists():
                return None
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract JSON data from markdown
            json_start = content.find('```json\n') + 8
            json_end = content.find('\n```', json_start)
            
            if json_start > 7 and json_end > json_start:
                json_data = content[json_start:json_end]
                return json.loads(json_data)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error loading resume analysis: {str(e)}")
            return None
    
    def save_score_report(self, email_id: str, score: float, breakdown: Dict[str, Any]) -> bool:
        """Save scoring report to markdown file."""
        try:
            candidate_dir = self.get_candidate_dir(email_id)
            score_file = candidate_dir / "score_report.md"
            
            content = f"""# Scoring Report

## Overall Score: {score:.1f}/100

## Score Breakdown
"""
            
            for category, details in breakdown.items():
                if isinstance(details, dict):
                    content += f"### {category.title()}\n"
                    content += f"- **Score**: {details.get('score', 0):.1f}\n"
                    content += f"- **Weight**: {details.get('weight', 0)}%\n"
                    if details.get('matches'):
                        content += f"- **Matches**: {', '.join(details['matches'])}\n"
                    content += "\n"
            
            content += f"""
---
<!-- JSON Data for programmatic access -->
```json
{json.dumps({'score': score, 'breakdown': breakdown}, indent=2)}
```
"""
            
            with open(score_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved score report for: {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving score report: {str(e)}")
            return False
    
    def load_score_report(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Load score report from markdown file."""
        try:
            score_file = self.get_candidate_dir(email_id) / "score_report.md"
            
            if not score_file.exists():
                return None
            
            with open(score_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract JSON data from markdown
            json_start = content.find('```json\n') + 8
            json_end = content.find('\n```', json_start)
            
            if json_start > 7 and json_end > json_start:
                json_data = content[json_start:json_end]
                return json.loads(json_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading score report: {str(e)}")
            return None
    
    def update_candidate_status(self, email_id: str, status: str, notes: str = "", tags: List[str] = None) -> bool:
        """Update candidate decision status."""
        try:
            candidate_dir = self.get_candidate_dir(email_id)
            decision_file = candidate_dir / "decision.md"
            
            if tags is None:
                tags = []
            
            content = f"""# Decision

## Status: {status.upper()}

## Notes
{notes or 'No notes provided.'}

## Tags
{', '.join(tags) if tags else 'No tags assigned.'}

## Updated
{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

---
<!-- JSON Data for programmatic access -->
```json
{json.dumps({
    'status': status,
    'notes': notes,
    'tags': tags,
    'updated_at': datetime.utcnow().isoformat()
}, indent=2)}
```
"""
            
            with open(decision_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Also update the metadata file
            candidate = self.load_candidate_metadata(email_id)
            if candidate:
                candidate.status = status
                candidate.notes = notes
                candidate.tags = tags
                candidate.updated_at = datetime.utcnow()
                self.save_candidate_metadata(candidate)
            
            logger.info(f"Updated status for {email_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating candidate status: {str(e)}")
            return False
    
    def list_all_candidates(self) -> List[CandidateData]:
        """List all candidates from the file system."""
        candidates = []
        
        try:
            if not self.candidates_dir.exists():
                return candidates
            
            for candidate_dir in self.candidates_dir.iterdir():
                if candidate_dir.is_dir() and candidate_dir.name != "index.md":
                    candidate = self.load_candidate_metadata(candidate_dir.name)
                    if candidate:
                        candidates.append(candidate)
            
            # Sort by email date (newest first)
            candidates.sort(key=lambda c: c.email_date or datetime.min, reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing candidates: {str(e)}")
        
        return candidates
    
    def log_processing(self, email_id: str, action: str, status: str, message: str = "") -> bool:
        """Log processing action to markdown file."""
        try:
            log_entry = ProcessingLogEntry(
                email_id=email_id,
                action=action,
                status=status,
                message=message
            )
            
            # Read existing log or create new
            log_content = ""
            if self.processing_log_file.exists():
                with open(self.processing_log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
            
            # If file is empty or doesn't exist, add header
            if not log_content.strip():
                log_content = "# Processing Log\n\n"
            
            # Add new entry
            timestamp = log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            new_entry = f"- **{timestamp}** | {email_id} | {action} | {status} | {message}\n"
            
            # Insert after header (find first line that starts with -)
            lines = log_content.split('\n')
            insert_index = 2  # After header and empty line
            
            for i, line in enumerate(lines):
                if line.startswith('- **'):
                    insert_index = i
                    break
            
            lines.insert(insert_index, new_entry.rstrip())
            
            with open(self.processing_log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging processing: {str(e)}")
            return False
    
    def update_index(self) -> bool:
        """Update the candidates index file."""
        try:
            candidates = self.list_all_candidates()
            
            content = f"""# Candidates Index

**Total Candidates**: {len(candidates)}
**Last Updated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Summary by Status
"""
            
            # Count by status
            status_counts = {}
            for candidate in candidates:
                status = candidate.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                content += f"- **{status.title()}**: {count}\n"
            
            content += "\n## Recent Candidates\n"
            
            # Show recent candidates (last 10)
            recent_candidates = candidates[:10]
            for candidate in recent_candidates:
                date_str = candidate.email_date.strftime('%Y-%m-%d') if candidate.email_date else 'N/A'
                score_str = f"{candidate.score:.1f}" if candidate.score > 0 else "Not scored"
                content += f"- **{candidate.candidate_name or 'Unknown'}** | {date_str} | Score: {score_str} | Status: {candidate.status}\n"
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating index: {str(e)}")
            return False


# Global file storage instance
file_storage = FileStorage() 