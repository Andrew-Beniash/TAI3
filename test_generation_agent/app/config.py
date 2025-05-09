"""
Configuration module for the application.
Loads environment variables and provides configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure DevOps Configuration
AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG")
AZURE_DEVOPS_PROJECT = os.getenv("AZURE_DEVOPS_PROJECT")
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")  # Personal Access Token
AZURE_DEVOPS_API_VERSION = os.getenv("AZURE_DEVOPS_API_VERSION", "7.0")  # Default to API version 7.0

# Vector DB Configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "weaviate")  # weaviate, qdrant, or faiss
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY", "")

# Embedding Service Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LangGraph Agent Configuration
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "./checkpoints")

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  # For validating Azure DevOps webhooks
