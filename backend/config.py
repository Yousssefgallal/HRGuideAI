import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


folder_path = r"C:\Users\Yossef\Downloads\copilotkit_template\docs"
FORMS_DIR = r"C:\Users\Yossef\Downloads\copilotkit_template\Forms"



# ===============================================
# LLM and RAG Settings
# ===============================================

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_CHUNKS = 3
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0

# ===============================================
# CORS Configuration
# ===============================================

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# ===============================================
# Environment Validation
# ===============================================

def validate_environment():
    """Validate required environment variables."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in a .env file or export it."
        )


