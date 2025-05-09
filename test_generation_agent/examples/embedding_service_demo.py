"""
Demo script for the embedding service.
Shows how to use the embedding service to generate embeddings for text.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the embedding service
from app.services.embedding import get_embedding, batch_get_embeddings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main function for the demo"""
    print("Embedding Service Demo")
    print("=====================")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it in the .env file.")
        return
    
    # Sample text for embedding
    user_story_text = """
    As a user, I want to reset my password so that I can regain access to my account if I forget it.
    
    Acceptance Criteria:
    1. User can access the password reset page from the login screen
    2. User can submit their email address to receive a password reset link
    3. User receives a password reset email with a secure, time-limited link
    4. User can create a new password that meets the security requirements
    5. User is notified when the password has been successfully reset
    """
    
    print("\nGenerating embedding for a user story...")
    embedding = await get_embedding(user_story_text)
    
    # Print the embedding information
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"Last 5 values: {embedding[-5:]}")
    
    # Try batch embeddings
    print("\nGenerating batch embeddings for multiple texts...")
    texts = [
        "As a user, I want to log in with my email and password.",
        "As a user, I want to register a new account with my email.",
        "As a user, I want to view my profile information."
    ]
    
    batch_embeddings = await batch_get_embeddings(texts)
    
    # Print batch embedding information
    print(f"Number of embeddings: {len(batch_embeddings)}")
    for i, emb in enumerate(batch_embeddings):
        print(f"Embedding {i+1} dimension: {len(emb)}")
    
    print("\nDemo complete!")

if __name__ == "__main__":
    asyncio.run(main())
