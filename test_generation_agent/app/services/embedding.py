"""
Embedding service for the QA Agent application.
Uses OpenAI or Sentence Transformers to create vector embeddings.
With enhanced caching and error handling capabilities.
"""
from typing import List, Dict, Union, Optional, Any, Tuple
import logging
import time
import hashlib
import json
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
import backoff
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import (
    OPENAI_API_KEY, 
    EMBEDDING_MODEL, 
    EMBEDDING_DIMENSIONS,
    EMBEDDING_CACHE_SIZE,
    BATCH_SIZE,
    MAX_RETRY_ATTEMPTS
)

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache for text embeddings with size limit."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize the cache with a maximum size."""
        self.cache: Dict[str, List[float]] = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _get_cache_key(self, text: str) -> str:
        """Create a consistent hash key for the text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Retrieve an embedding from the cache."""
        key = self._get_cache_key(text)
        result = self.cache.get(key)
        if result is not None:
            self.hits += 1
            logger.debug(f"Cache hit for text: {text[:50]}...")
        else:
            self.misses += 1
            logger.debug(f"Cache miss for text: {text[:50]}...")
        return result
    
    def set(self, text: str, embedding: List[float]) -> None:
        """Store an embedding in the cache."""
        key = self._get_cache_key(text)
        
        # Implement LRU-like behavior by removing oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            # Remove first key (oldest) in the dictionary
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            logger.debug(f"Cache full, removed oldest entry")
        
        self.cache[key] = embedding
        logger.debug(f"Cached embedding for text: {text[:50]}...")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class EmbeddingService:
    """Service for creating vector embeddings from text with caching."""
    
    def __init__(self, model_name: Optional[str] = None, cache_size: int = None):
        """Initialize the embedding service with the specified model and cache."""
        self.model_name = model_name or EMBEDDING_MODEL
        cache_size = cache_size or EMBEDDING_CACHE_SIZE
        self.cache = EmbeddingCache(max_size=cache_size)
        self.batch_size = BATCH_SIZE
        self.retry_attempts = MAX_RETRY_ATTEMPTS
        
        try:
            if "text-embedding" in self.model_name:
                logger.info(f"Using OpenAI embedding model: {self.model_name}")
                self.embedder = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=OPENAI_API_KEY
                )
                self.is_openai = True
            else:
                logger.info(f"Using SentenceTransformers embedding model: {self.model_name}")
                self.embedder = SentenceTransformer(self.model_name)
                self.is_openai = False
                
            # Test the model to ensure it's properly loaded
            self._test_embedding()
            
            logger.info(f"Embedding service initialized successfully with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _test_embedding(self) -> None:
        """Test the embedding model with a simple input."""
        try:
            test_text = "Test embedding model initialization"
            if self.is_openai:
                test_result = self.embedder.embed_query(test_text)
            else:
                test_result = self.embedder.encode(test_text).tolist()
            
            dim = len(test_result)
            expected_dim = EMBEDDING_DIMENSIONS
            logger.info(f"Test embedding successful. Dimension: {dim}, Expected: {expected_dim}")
            
            if dim != expected_dim:
                logger.warning(f"Embedding dimension mismatch. Got {dim}, expected {expected_dim}")
        except Exception as e:
            logger.error(f"Test embedding failed: {e}")
            raise
    
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def _embed_text_with_retry(self, text: str) -> List[float]:
        """Create an embedding for a single text with retry logic."""
        try:
            if self.is_openai:
                return self.embedder.embed_query(text)
            else:
                return self.embedder.encode(text).tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e} for text: {text[:100]}...")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Create an embedding for a single text, using cache if available."""
        # Check cache first
        cached_embedding = self.cache.get(text)
        if cached_embedding is not None:
            return cached_embedding
        
        # Generate new embedding
        embedding = self._embed_text_with_retry(text)
        
        # Store in cache
        self.cache.set(text, embedding)
        
        return embedding
    
    def _batch_embed(self, texts: List[str], start_idx: int, end_idx: int) -> Tuple[List[List[float]], List[int]]:
        """Process a batch of embeddings."""
        batch_texts = texts[start_idx:end_idx]
        batch_indices = list(range(start_idx, end_idx))
        
        # Skip texts that are in cache
        to_embed_texts = []
        to_embed_indices = []
        results = [None] * len(batch_texts)
        
        # Check cache for each text
        for i, text in enumerate(batch_texts):
            cached = self.cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                to_embed_texts.append(text)
                to_embed_indices.append(i)
        
        # If there are texts to embed
        if to_embed_texts:
            try:
                if self.is_openai:
                    embeddings = self.embedder.embed_documents(to_embed_texts)
                else:
                    embeddings = self.embedder.encode(to_embed_texts).tolist()
                
                # Store results and update cache
                for i, idx in enumerate(to_embed_indices):
                    results[idx] = embeddings[i]
                    self.cache.set(batch_texts[idx], embeddings[i])
            
            except Exception as e:
                logger.error(f"Batch embedding error: {e}")
                # Fall back to individual embedding if batch fails
                for i, idx in enumerate(to_embed_indices):
                    try:
                        embedding = self._embed_text_with_retry(batch_texts[idx])
                        results[idx] = embedding
                        self.cache.set(batch_texts[idx], embedding)
                    except Exception as inner_e:
                        logger.error(f"Individual embedding failed for text {idx}: {inner_e}")
                        # Use a zero vector as fallback (not ideal but prevents crashing)
                        results[idx] = [0.0] * EMBEDDING_DIMENSIONS
        
        return results, batch_indices
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts with optimized batching and caching."""
        if not texts:
            return []
        
        # Initialize results array
        results = [None] * len(texts)
        
        # Process in batches
        batch_size = self.batch_size
        
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(0, len(texts), batch_size):
                end_idx = min(i + batch_size, len(texts))
                futures.append(
                    executor.submit(self._batch_embed, texts, i, end_idx)
                )
            
            # Collect results
            for future in futures:
                batch_results, batch_indices = future.result()
                for i, idx in enumerate(batch_indices):
                    if idx < len(results):
                        results[idx] = batch_results[i]
        
        # Verify all results are set
        for i, r in enumerate(results):
            if r is None:
                logger.error(f"Missing embedding for text at index {i}")
                results[i] = [0.0] * EMBEDDING_DIMENSIONS
        
        return results
    
    def embed_user_story(self, title: str, description: str) -> List[float]:
        """Create an embedding for a user story combining title and description."""
        full_text = f"Title: {title}\nDescription: {description}"
        return self.embed_text(full_text)
    
    def embed_test_case(self, title: str, description: str, steps: str, expected_result: str) -> List[float]:
        """Create an embedding for a test case."""
        full_text = f"Title: {title}\nDescription: {description}\nSteps: {steps}\nExpected Result: {expected_result}"
        return self.embed_text(full_text)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache usage."""
        return self.cache.get_stats()


# Create a singleton instance with LRU cache for the factory function
@lru_cache(maxsize=1)
def get_embedding_service(model_name: Optional[str] = None, cache_size: Optional[int] = None) -> EmbeddingService:
    """Get a cached instance of the embedding service."""
    logger.info(f"Creating embedding service with model {model_name or EMBEDDING_MODEL}")
    return EmbeddingService(model_name, cache_size)
