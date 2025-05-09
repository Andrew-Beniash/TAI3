"""
Launch script for the test generation agent application.
This script starts the FastAPI application using uvicorn.
"""
import uvicorn
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    logger.info("Loaded environment variables from .env file")

def main():
    """Main function to start the application"""
    # Get the host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting Test Generation Agent on {host}:{port}")
    
    # Start the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True if os.getenv("DEBUG", "false").lower() == "true" else False
    )

if __name__ == "__main__":
    main()
