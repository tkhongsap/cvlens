"""AI prompts for resume analysis and processing."""

# System prompt for comprehensive resume analysis
COMPREHENSIVE_ANALYSIS_PROMPT = """Analyze this resume/CV and provide a comprehensive candidate report in JSON format with the following structure:

{
  "personal_info": {
    "name": "Full name of candidate",
    "email": "email@example.com",
    "phone": "+1234567890"
  },
  "executive_summary": "2-3 sentence summary of the candidate's profile and career focus",
  "experience_highlights": [
    "Key achievement or role 1",
    "Key achievement or role 2",
    "Key achievement or role 3"
  ],
  "education_highlights": [
    "Degree/certification 1",
    "Degree/certification 2"
  ],
  "key_skills": [
    "skill1", "skill2", "skill3", "skill4", "skill5"
  ],
  "interesting_facts": [
    "Notable project or achievement",
    "Unique background or experience",
    "Awards or recognitions"
  ],
  "raw_text": "Full extracted text from the resume for reference"
}

Focus on extracting the most relevant and impressive information. If any section is not available, use empty arrays or null values."""

# Future prompts can be added here:
# SKILLS_EXTRACTION_PROMPT = "..."
# EXPERIENCE_ANALYSIS_PROMPT = "..."
# EDUCATION_VERIFICATION_PROMPT = "..." 