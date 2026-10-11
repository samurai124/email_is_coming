import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
RESUMES_DIR = DATA_DIR / "resumes"

# Load .env file
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

class Config:
    # Sender details
    SENDER_NAME = os.getenv("SENDER_NAME", "Your Name")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
    SENDER_PHONE = os.getenv("SENDER_PHONE", "")
    SENDER_LINKEDIN = os.getenv("SENDER_LINKEDIN", "")
    SENDER_PORTFOLIO = os.getenv("SENDER_PORTFOLIO", "")
    
    # Candidate profile summary for AI personalization
    CANDIDATE_SUMMARY = os.getenv(
        "CANDIDATE_SUMMARY",
        "Motivated professional seeking new opportunities with experience in software development, problem solving, and building scalable applications."
    )
    
    # SMTP Server Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # AI Personalization (Google Gemini API)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Resume Attachment
    RESUME_FILENAME = os.getenv("RESUME_FILENAME", "resume.pdf")
    RESUME_PATH = RESUMES_DIR / RESUME_FILENAME
    
    # CSV paths
    CSV_PATH = DATA_DIR / os.getenv("CSV_FILENAME", "companies.csv")
    LOG_PATH = DATA_DIR / "sent_log.csv"
    
    # Delivery & Anti-Spam Safeguards
    MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "20"))
    MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "45"))
    DAILY_MAX_EMAILS = int(os.getenv("DAILY_MAX_EMAILS", "40"))

    @classmethod
    def validate_setup(cls) -> list[str]:
        """Checks for missing critical configurations."""
        issues = []
        if not cls.SENDER_EMAIL:
            issues.append("SENDER_EMAIL is not set in .env")
        if not cls.SENDER_PASSWORD:
            issues.append("SENDER_PASSWORD is not set in .env (Use a Gmail App Password)")
        if not cls.RESUME_PATH.exists():
            issues.append(f"Resume file not found at: {cls.RESUME_PATH}")
        if not cls.CSV_PATH.exists():
            issues.append(f"Companies CSV not found at: {cls.CSV_PATH}")
        return issues
