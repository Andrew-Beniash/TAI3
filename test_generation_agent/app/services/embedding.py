"""
Embedding service module.
Handles text embedding generation using OpenAI's embedding models or Sentence Transformers.
"""
import logging
from typing import List, Union, Dict, Any
import os
import asyncio

from app.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL

# Configure logging
logger = logging.getLogger(__name__)

# Check if OpenAI API key is available
has_openai = bool(OPENAI_API_KEY)

# Try to import OpenAI
try:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=OPENAI_API_KEY) if has_openai else None
except ImportError:
    logger.warning("OpenAI package not installed. Will fall back to Sentence Transformers if available.")
    has_openai = False
    client = None

# Try to import Sentence Transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    model = None  # Will be lazy-loaded when needed
except ImportError:
    logger.warning("Sentence Transformers package not installed. Need either OpenAI or Sentence Transformers.")
    model = None

async def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a text using either OpenAI or Sentence Transformers.
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    if not text:
        raise ValueError("Cannot embed empty text")
        
    # Try OpenAI first if available
    if has_openai and client:
        try:
            return await get_openai_embedding(text)
        except Exception as e:
            logger.error(f"Error using OpenAI embedding: {e}")
            # Fall back to Sentence Transformers
            return await get_sentence_transformer_embedding(text)
    else:
        # Use Sentence Transformers directly
        return await get_sentence_transformer_embedding(text)

async def get_openai_embedding(text: str) -> List[float]:
    """
    Get embedding using OpenAI API.
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    try:
        response = await client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting OpenAI embedding: {e}", exc_info=True)
        raise

async def get_sentence_transformer_embedding(text: str) -> List[float]:
    """
    Get embedding using Sentence Transformers.
    
    Args:
        text: The text to embed
        
    Returns:
        List[float]: The embedding vector
    """
    global model
    
    try:
        # Lazy-load the model when first needed
        if model is None:
            # Use a separate thread for loading the model
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, lambda: SentenceTransformer('all-MiniLM-L6-v2'))
            
        # Run the model in a separate thread
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, lambda: model.encode(text).tolist())
        return embedding
    except Exception as e:
        logger.error(f"Error getting Sentence Transformer embedding: {e}", exc_info=True)
        raise

async def batch_get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts in a batch.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List[List[float]]: List of embedding vectors
    """
    if not texts:
        return []
        
    # Filter out empty texts
    valid_texts = [text for text in texts if text]
    
    if not valid_texts:
        return []
        
    # Use OpenAI batch API if available
    if has_openai and client:
        try:
            response = await client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=valid_texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error getting batch OpenAI embeddings: {e}", exc_info=True)
            # Fall back to Sentence Transformers
    
    # Use Sentence Transformers
    global model
    try:
        # Lazy-load the model when first needed
        if model is None:
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, lambda: SentenceTransformer('all-MiniLM-L6-v2'))
            
        # Run the model in a separate thread
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, lambda: model.encode(valid_texts).tolist())
        return embeddings
    except Exception as e:
        logger.error(f"Error getting batch Sentence Transformer embeddings: {e}", exc_info=True)
        raise
