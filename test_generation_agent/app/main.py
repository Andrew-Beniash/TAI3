"""
Main entry point for the FastAPI application.
Configures the API endpoints and middleware.
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import PROJECT_NAME, API_PREFIX, validate_config
from app.routes.webhook import router as webhook_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=PROJECT_NAME,
    description="API for test case generation using LangGraph and Azure DevOps integration",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix=API_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Runs when the application starts"""
    logger.info(f"Starting {PROJECT_NAME}")
    
    # Validate configuration
    if not validate_config():
        logger.warning("Configuration is incomplete. Some features may not work correctly.")

@app.get("/")
async def root():
    """Root endpoint for quick health check"""
    return {"status": "ok", "message": f"Welcome to {PROJECT_NAME}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
