"""
Configuration settings for the test generation agent.
Loads environment variables and provides centralized configuration management.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# API Configuration
API_PREFIX = "/api/v1"
PROJECT_NAME = "Test Generation Agent"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Azure DevOps Settings
AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG", "")
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT", "")  # Personal Access Token
AZURE_DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT", "")

# OpenAI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_COMPLETION_MODEL = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4")

# Vector DB Settings
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "weaviate")  # weaviate, qdrant, or faiss
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "")
VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY", "")

# Webhook Security
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

def get_azure_devops_credentials():
    """Returns Azure DevOps credentials as a dictionary"""
    return {
        "organization": AZURE_DEVOPS_ORG,
        "project": AZURE_DEVOPS_PROJECT,
        "personal_access_token": AZURE_DEVOPS_PAT
    }

def get_vector_db_credentials():
    """Returns Vector DB credentials as a dictionary"""
    return {
        "type": VECTOR_DB_TYPE,
        "url": VECTOR_DB_URL,
        "api_key": VECTOR_DB_API_KEY
    }

# Validate required configuration
def validate_config() -> bool:
    """Validates that all required configuration is present"""
    if not OPENAI_API_KEY:
        print("WARNING: OPENAI_API_KEY is not set")
        return False
        
    if not all([AZURE_DEVOPS_ORG, AZURE_DEVOPS_PAT, AZURE_DEVOPS_PROJECT]):
        print("WARNING: Azure DevOps credentials are incomplete")
        return False
        
    if not VECTOR_DB_URL:
        print("WARNING: Vector database URL is not set")
        return False
        
    return True

# Example usage in app startup
# if not validate_config():
#     print("Configuration is incomplete. Some features may not work.")
