"""Scoring service for calculating candidate match scores."""

import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.config import config
from src.models.database import db, Candidate

logger = logging.getLogger(__name__)


class CandidateScorer:
    """Service for scoring candidates against job profiles."""
    
    def __init__(self):
        self.job_profile = self._load_job_profile()
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    def _load_job_profile(self) -> Dict[str, Any]:
        """Load job profile from YAML file."""
        try:
            with open(config.job_profile_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading job profile: {str(e)}")
            return {}
    
    def score_all_pending(self) -> Tuple[int, int]:
        """
        Score all parsed but unscored candidates.
        
        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0
        
        with db.get_session() as session:
            # Get parsed but unscored candidates
            candidates = session.query(Candidate).filter(
                Candidate.is_parsed == True,
                Candidate.is_scored == False
            ).all()
            
            for candidate in candidates:
                try:
                    # Calculate score
                    score, breakdown = self.score_candidate(candidate)
                    
                    # Update candidate
                    candidate.score = score
                    candidate.score_breakdown = db.cipher.encrypt(json.dumps(breakdown))
                    candidate.is_scored = True
                    
                    success_count += 1
                    logger.info(f"Scored {candidate.resume_filename}: {score:.2f}")
                    
                    db.log_processing(
                        session,
                        candidate.email_id,
                        'score',
                        'success',
                        f'Score: {score:.2f}'
                    )
                    
                except Exception as e:
                    logger.error(f"Error scoring candidate {candidate.id}: {str(e)}")
                    error_count += 1
                    
                    db.log_processing(
                        session,
                        candidate.email_id,
                        'score',
                        'failed',
                        str(e)
                    )
            
            session.commit()
        
        logger.info(f"Scoring completed: {success_count} success, {error_count} errors")
        return success_count, error_count
    
    def score_candidate(self, candidate: Candidate) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate match score for a candidate.
        
        Returns:
            Tuple of (total_score, score_breakdown)
        """
        # Get weights from job profile
        weights = self.job_profile.get('weights', {
            'skills': 60,
            'education': 20,
            'experience': 20
        })
        
        # Decrypt candidate data
        candidate_dict = candidate.to_dict(db.cipher)
        
        # Calculate component scores
        skills_score = self._score_skills(candidate_dict)
        education_score = self._score_education(candidate_dict)
        experience_score = self._score_experience(candidate_dict)
        
        # Calculate weighted total
        total_score = (
            skills_score * weights['skills'] / 100 +
            education_score * weights['education'] / 100 +
            experience_score * weights['experience'] / 100
        )
        
        # Create breakdown
        breakdown = {
            'skills': {
                'score': skills_score,
                'weight': weights['skills'],
                'weighted_score': skills_score * weights['skills'] / 100,
                'matched_skills': self._get_matched_skills(candidate_dict)
            },
            'education': {
                'score': education_score,
                'weight': weights['education'],
                'weighted_score': education_score * weights['education'] / 100,
                'matched_degrees': self._get_matched_education(candidate_dict)
            },
            'experience': {
                'score': experience_score,
                'weight': weights['experience'],
                'weighted_score': experience_score * weights['experience'] / 100,
                'total_years': self._get_total_experience_years(candidate_dict)
            },
            'total_score': total_score * 100  # Convert to 0-100 scale
        }
        
        return total_score * 100, breakdown
    
    def _score_skills(self, candidate: Dict[str, Any]) -> float:
        """Score candidate skills against job requirements."""
        job_skills = self.job_profile.get('skills', {})
        required_skills = [s.lower() for s in job_skills.get('required', [])]
        preferred_skills = [s.lower() for s in job_skills.get('preferred', [])]
        nice_to_have = [s.lower() for s in job_skills.get('nice_to_have', [])]
        
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        
        if not required_skills and not preferred_skills:
            return 0.5  # Default score if no skills defined
        
        # Calculate matches
        required_matches = sum(1 for skill in required_skills if skill in candidate_skills)
        preferred_matches = sum(1 for skill in preferred_skills if skill in candidate_skills)
        nice_matches = sum(1 for skill in nice_to_have if skill in candidate_skills)
        
        # Calculate score (required skills are most important)
        score = 0.0
        
        if required_skills:
            score += (required_matches / len(required_skills)) * 0.6
        
        if preferred_skills:
            score += (preferred_matches / len(preferred_skills)) * 0.3
        
        if nice_to_have:
            score += (nice_matches / len(nice_to_have)) * 0.1
        
        # Bonus for having many relevant skills
        total_relevant = required_matches + preferred_matches + nice_matches
        if total_relevant > 5:
            score = min(1.0, score * 1.1)
        
        return min(1.0, score)
    
    def _score_education(self, candidate: Dict[str, Any]) -> float:
        """Score candidate education against job requirements."""
        job_education = self.job_profile.get('education', {})
        required_edu = [e.lower() for e in job_education.get('required', [])]
        preferred_edu = [e.lower() for e in job_education.get('preferred', [])]
        
        candidate_education = candidate.get('education', [])
        education_text = ' '.join([e.get('text', '').lower() for e in candidate_education])
        
        if not education_text:
            return 0.0
        
        # Check for required education
        required_score = 0.0
        for req in required_edu:
            if req in education_text:
                required_score = 0.7
                break
        
        # Check for preferred education
        preferred_score = 0.0
        for pref in preferred_edu:
            if pref in education_text:
                preferred_score = 0.3
                break
        
        return min(1.0, required_score + preferred_score)
    
    def _score_experience(self, candidate: Dict[str, Any]) -> float:
        """Score candidate experience against job requirements."""
        job_experience = self.job_profile.get('experience', {})
        min_years = job_experience.get('minimum_years', 0)
        pref_years = job_experience.get('preferred_years', min_years)
        required_domains = [d.lower() for d in job_experience.get('required_domains', [])]
        
        # Calculate total years of experience
        total_years = self._get_total_experience_years(candidate)
        
        # Score based on years
        if total_years >= pref_years:
            years_score = 1.0
        elif total_years >= min_years:
            years_score = 0.7 + (total_years - min_years) / (pref_years - min_years) * 0.3
        else:
            years_score = total_years / min_years * 0.7 if min_years > 0 else 0.5
        
        # Check for domain experience
        resume_text = candidate.get('resume_text', '').lower()
        domain_matches = sum(1 for domain in required_domains if domain in resume_text)
        domain_score = domain_matches / len(required_domains) if required_domains else 1.0
        
        # Combine scores
        return min(1.0, years_score * 0.7 + domain_score * 0.3)
    
    def _get_matched_skills(self, candidate: Dict[str, Any]) -> List[str]:
        """Get list of matched skills."""
        job_skills = self.job_profile.get('skills', {})
        all_job_skills = (
            job_skills.get('required', []) +
            job_skills.get('preferred', []) +
            job_skills.get('nice_to_have', [])
        )
        all_job_skills = [s.lower() for s in all_job_skills]
        
        candidate_skills = [s.lower() for s in candidate.get('skills', [])]
        
        return [skill for skill in candidate_skills if skill in all_job_skills]
    
    def _get_matched_education(self, candidate: Dict[str, Any]) -> List[str]:
        """Get list of matched education credentials."""
        job_education = self.job_profile.get('education', {})
        all_edu = job_education.get('required', []) + job_education.get('preferred', [])
        
        matched = []
        candidate_education = candidate.get('education', [])
        
        for edu in candidate_education:
            edu_text = edu.get('text', '').lower()
            for req in all_edu:
                if req.lower() in edu_text:
                    matched.append(edu.get('text', ''))
                    break
        
        return matched
    
    def _get_total_experience_years(self, candidate: Dict[str, Any]) -> float:
        """Calculate total years of experience."""
        experience = candidate.get('experience', [])
        
        if not experience:
            # Try to extract from resume text
            resume_text = candidate.get('resume_text', '')
            import re
            
            # Look for patterns like "X years of experience"
            years_pattern = re.compile(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', re.IGNORECASE)
            match = years_pattern.search(resume_text)
            if match:
                return float(match.group(1))
            
            return 0.0
        
        # Sum up years from parsed experience
        total_years = sum(exp.get('years', 0) for exp in experience)
        return total_years
    
    def calculate_tfidf_similarity(self, candidate_text: str, job_description: str) -> float:
        """Calculate TF-IDF similarity between candidate and job description."""
        try:
            # Create corpus
            corpus = [candidate_text, job_description]
            
            # Fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {str(e)}")
            return 0.0


# Global scorer instance
candidate_scorer = CandidateScorer() 