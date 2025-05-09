"""
Test suite for the Embedding Service.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from app.services.embedding import EmbeddingService, EmbeddingCache, get_embedding_service
from app.config import EMBEDDING_DIMENSIONS

# Constants for testing
TEST_TEXT = "This is a sample text for embedding tests"
TEST_TEXTS = [
    "First sample text for embedding",
    "Second sample text for embedding",
    "Third sample text for embedding",
    "Fourth sample text for embedding"
]
TEST_STORY_TITLE = "User can view test results"
TEST_STORY_DESCRIPTION = "As a QA engineer, I want to view test results in a dashboard"
TEST_CASE_TITLE = "Verify test results display"
TEST_CASE_DESCRIPTION = "Test that results display correctly"
TEST_CASE_STEPS = "1. Login\n2. Navigate to dashboard\n3. Check results"
TEST_CASE_EXPECTED = "Results should be displayed with correct formatting"


@pytest.fixture
def mock_openai_embeddings():
    """Create a mock OpenAIEmbeddings instance."""
    mock = MagicMock()
    # Generate fake embeddings with correct dimensions
    mock.embed_query.return_value = [0.1] * EMBEDDING_DIMENSIONS
    mock.embed_documents.return_value = [[0.1] * EMBEDDING_DIMENSIONS for _ in range(4)]
    return mock


@pytest.fixture
def mock_sentence_transformer():
    """Create a mock SentenceTransformer instance."""
    mock = MagicMock()
    # Generate fake embeddings with correct dimensions
    mock.encode.return_value = np.array([[0.2] * EMBEDDING_DIMENSIONS for _ in range(1)]).reshape(-1).tolist()
    return mock


class TestEmbeddingCache:
    """Test suite for the EmbeddingCache class."""
    
    def test_cache_initialization(self):
        """Test that the cache initializes correctly."""
        cache = EmbeddingCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
    
    def test_cache_set_get(self):
        """Test setting and getting values from the cache."""
        cache = EmbeddingCache(max_size=10)
        test_embedding = [0.1, 0.2, 0.3]
        
        # Set a value
        cache.set(TEST_TEXT, test_embedding)
        
        # Get the value
        result = cache.get(TEST_TEXT)
        assert result == test_embedding
        assert cache.hits == 1
        assert cache.misses == 0
    
    def test_cache_miss(self):
        """Test cache miss behavior."""
        cache = EmbeddingCache(max_size=10)
        result = cache.get(TEST_TEXT)
        assert result is None
        assert cache.hits == 0
        assert cache.misses == 1
    
    def test_cache_lru_behavior(self):
        """Test LRU behavior when cache is full."""
        cache = EmbeddingCache(max_size=2)
        
        # Fill the cache
        cache.set("text1", [0.1])
        cache.set("text2", [0.2])
        
        # Add one more item to trigger LRU removal
        cache.set("text3", [0.3])
        
        # First item should be removed
        assert cache.get("text1") is None
        assert cache.get("text2") is not None
        assert cache.get("text3") is not None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = EmbeddingCache(max_size=5)
        
        # Add some items
        cache.set("text1", [0.1])
        cache.set("text2", [0.2])
        
        # Get some items (hits and misses)
        cache.get("text1")  # hit
        cache.get("text3")  # miss
        
        # Check stats
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 5
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestEmbeddingService:
    """Test suite for the EmbeddingService class."""
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_init_with_openai(self, mock_openai_class):
        """Test initialization with OpenAI model."""
        mock_openai_class.return_value = mock_openai_embeddings()
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        assert service.is_openai is True
        assert service.model_name == "text-embedding-3-small"
        mock_openai_class.assert_called_once()
    
    @patch("app.services.embedding.SentenceTransformer")
    def test_init_with_sentence_transformer(self, mock_st_class):
        """Test initialization with SentenceTransformer model."""
        mock_st_class.return_value = mock_sentence_transformer()
        
        service = EmbeddingService(model_name="all-MiniLM-L6-v2")
        assert service.is_openai is False
        assert service.model_name == "all-MiniLM-L6-v2"
        mock_st_class.assert_called_once()
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_embed_text(self, mock_openai_class):
        """Test embedding a single text."""
        mock_embedder = mock_openai_embeddings()
        mock_openai_class.return_value = mock_embedder
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        embedding = service.embed_text(TEST_TEXT)
        
        assert len(embedding) == EMBEDDING_DIMENSIONS
        mock_embedder.embed_query.assert_called_once_with(TEST_TEXT)
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_embed_texts(self, mock_openai_class):
        """Test embedding multiple texts."""
        mock_embedder = mock_openai_embeddings()
        mock_openai_class.return_value = mock_embedder
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        embeddings = service.embed_texts(TEST_TEXTS)
        
        assert len(embeddings) == len(TEST_TEXTS)
        assert all(len(emb) == EMBEDDING_DIMENSIONS for emb in embeddings)
        mock_embedder.embed_documents.assert_called_once()
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_embed_user_story(self, mock_openai_class):
        """Test embedding a user story."""
        mock_embedder = mock_openai_embeddings()
        mock_openai_class.return_value = mock_embedder
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        embedding = service.embed_user_story(TEST_STORY_TITLE, TEST_STORY_DESCRIPTION)
        
        assert len(embedding) == EMBEDDING_DIMENSIONS
        expected_text = f"Title: {TEST_STORY_TITLE}\nDescription: {TEST_STORY_DESCRIPTION}"
        mock_embedder.embed_query.assert_called_once_with(expected_text)
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_embed_test_case(self, mock_openai_class):
        """Test embedding a test case."""
        mock_embedder = mock_openai_embeddings()
        mock_openai_class.return_value = mock_embedder
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        embedding = service.embed_test_case(
            TEST_CASE_TITLE, 
            TEST_CASE_DESCRIPTION, 
            TEST_CASE_STEPS, 
            TEST_CASE_EXPECTED
        )
        
        assert len(embedding) == EMBEDDING_DIMENSIONS
        expected_text = (
            f"Title: {TEST_CASE_TITLE}\n"
            f"Description: {TEST_CASE_DESCRIPTION}\n"
            f"Steps: {TEST_CASE_STEPS}\n"
            f"Expected Result: {TEST_CASE_EXPECTED}"
        )
        mock_embedder.embed_query.assert_called_once_with(expected_text)
    
    @patch("app.services.embedding.OpenAIEmbeddings")
    def test_caching(self, mock_openai_class):
        """Test that caching works correctly."""
        mock_embedder = mock_openai_embeddings()
        mock_openai_class.return_value = mock_embedder
        
        service = EmbeddingService(model_name="text-embedding-3-small")
        
        # First call should hit the API
        service.embed_text(TEST_TEXT)
        assert mock_embedder.embed_query.call_count == 1
        
        # Second call should use cache
        service.embed_text(TEST_TEXT)
        assert mock_embedder.embed_query.call_count == 1  # Still 1, not increased
        
        # Check cache stats
        stats = service.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns a singleton."""
        with patch("app.services.embedding.EmbeddingService") as mock_service_class:
            mock_service_class.return_value = MagicMock()
            
            # Call twice with the same parameters
            service1 = get_embedding_service("test-model")
            service2 = get_embedding_service("test-model")
            
            # Should create only one instance
            assert mock_service_class.call_count == 1
            assert service1 is service2
            
            # Different parameters should create a new instance
            service3 = get_embedding_service("different-model")
            assert mock_service_class.call_count == 2
            assert service1 is not service3
