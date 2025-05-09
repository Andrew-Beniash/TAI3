"""
Test script for the embedding service.
"""
import sys
import os
from pathlib import Path
import pytest
import asyncio

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the embedding service
from app.services.embedding import get_embedding, batch_get_embeddings

@pytest.mark.asyncio
async def test_get_embedding():
    """Test getting embeddings for a single text"""
    # Skip test if OpenAI API key is not set
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not set")
    
    # Test text
    text = "This is a test text for embedding."
    
    # Get embedding
    embedding = await get_embedding(text)
    
    # Check if embedding is a list of floats
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)

@pytest.mark.asyncio
async def test_batch_get_embeddings():
    """Test getting embeddings for multiple texts"""
    # Skip test if OpenAI API key is not set
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not set")
    
    # Test texts
    texts = [
        "This is the first test text.",
        "This is the second test text.",
        "This is the third test text."
    ]
    
    # Get embeddings
    embeddings = await batch_get_embeddings(texts)
    
    # Check if embeddings is a list of lists of floats
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(texts)
    assert all(isinstance(emb, list) for emb in embeddings)
    assert all(all(isinstance(x, float) for x in emb) for emb in embeddings)

@pytest.mark.asyncio
async def test_get_embedding_empty_text():
    """Test getting embeddings for empty text"""
    # Test with empty text
    with pytest.raises(ValueError):
        await get_embedding("")

@pytest.mark.asyncio
async def test_batch_get_embeddings_empty_list():
    """Test getting embeddings for empty list"""
    # Test with empty list
    embeddings = await batch_get_embeddings([])
    assert embeddings == []

@pytest.mark.asyncio
async def test_batch_get_embeddings_with_empty_texts():
    """Test getting embeddings with some empty texts"""
    # Skip test if OpenAI API key is not set
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not set")
    
    # Test texts with some empty strings
    texts = [
        "This is a valid text.",
        "",
        "This is another valid text."
    ]
    
    # Get embeddings
    embeddings = await batch_get_embeddings(texts)
    
    # Check if embeddings has the correct number of items (only valid texts)
    assert isinstance(embeddings, list)
    assert len(embeddings) <= len(texts)  # Less or equal because empty texts are skipped
    if len(embeddings) > 0:
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(all(isinstance(x, float) for x in emb) for emb in embeddings)

if __name__ == "__main__":
    # Run the tests manually
    asyncio.run(test_get_embedding())
    asyncio.run(test_batch_get_embeddings())
