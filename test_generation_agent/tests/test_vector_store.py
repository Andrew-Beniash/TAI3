"""
Tests for the vector store service.
"""
import os
import pytest
from datetime import datetime
import uuid
from unittest.mock import patch, MagicMock

from app.models.data_models import UserStory, TestCase
from app.services.vector_store import (
    VectorStoreService, QdrantVectorStore, WeaviateVectorStore, get_vector_store
)
from app.config import VECTOR_DB_TYPE

# Sample test data
SAMPLE_USER_STORY = UserStory(
    story_id="test-story-123",
    project_id="test-project-456",
    title="User can reset password",
    description="As a user, I want to be able to reset my password if I forget it.",
    created_at=datetime.now()
)

SAMPLE_TEST_CASE = TestCase(
    test_id="test-case-789",
    story_id="test-story-123",
    title="Password Reset - Valid Email",
    description="Test the password reset functionality with a valid email address",
    steps=[
        {"step": "1", "description": "Navigate to the login page"},
        {"step": "2", "description": "Click on 'Forgot Password' link"},
        {"step": "3", "description": "Enter a valid email address"},
        {"step": "4", "description": "Click 'Submit' button"}
    ],
    expected_result="User should receive a password reset email",
    test_type="positive",
    test_case_text="# Password Reset - Valid Email\n\nTest the password reset functionality with a valid email address",
    test_case_csv="Step,Description,Expected Result\n1,Navigate to login page,Login page displayed\n..."
)

# Mock embedding vector
MOCK_EMBEDDING = [0.1] * 1536

@pytest.fixture
def mock_embedding_service():
    """Fixture to mock the embedding service."""
    with patch("app.services.vector_store.get_embedding_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.embed_user_story.return_value = MOCK_EMBEDDING
        mock_service.embed_test_case.return_value = MOCK_EMBEDDING
        mock_service.embed_text.return_value = MOCK_EMBEDDING
        mock_service.embed_texts.return_value = [MOCK_EMBEDDING]
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_qdrant_client():
    """Fixture to mock the Qdrant client."""
    with patch("app.services.vector_store.QdrantClient") as mock_client_class:
        mock_client = MagicMock()
        # Mock collections response
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        # Setup mock client instance
        mock_client_class.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_weaviate_client():
    """Fixture to mock the Weaviate client."""
    with patch("app.services.vector_store.weaviate.Client") as mock_client_class:
        mock_client = MagicMock()
        # Mock schema
        mock_schema = MagicMock()
        mock_schema.exists.return_value = False
        mock_schema.get.return_value = {"classes": []}
        mock_client.schema = mock_schema
        # Mock data object
        mock_data_object = MagicMock()
        mock_client.data_object = mock_data_object
        # Mock query builder
        mock_query = MagicMock()
        mock_client.query = mock_query
        # Setup mock client instance
        mock_client_class.return_value = mock_client
        yield mock_client

class TestQdrantVectorStore:
    """Tests for the QdrantVectorStore class."""
    
    def test_init_creates_collections(self, mock_embedding_service, mock_qdrant_client):
        """Test that the constructor creates collections if they don't exist."""
        store = QdrantVectorStore()
        assert mock_qdrant_client.get_collections.called
        assert mock_qdrant_client.create_collection.called
    
    def test_store_user_story(self, mock_embedding_service, mock_qdrant_client):
        """Test storing a user story."""
        store = QdrantVectorStore()
        result = store.store_user_story(SAMPLE_USER_STORY)
        
        assert result == SAMPLE_USER_STORY.story_id
        assert mock_qdrant_client.upsert.called
        upsert_args = mock_qdrant_client.upsert.call_args[1]
        assert upsert_args["collection_name"] == "user_stories"
        assert len(upsert_args["points"]) == 1
    
    def test_store_test_case(self, mock_embedding_service, mock_qdrant_client):
        """Test storing a test case."""
        store = QdrantVectorStore()
        result = store.store_test_case(SAMPLE_TEST_CASE)
        
        assert result == SAMPLE_TEST_CASE.test_id
        assert mock_qdrant_client.upsert.called
        upsert_args = mock_qdrant_client.upsert.call_args[1]
        assert upsert_args["collection_name"] == "test_cases"
        assert len(upsert_args["points"]) == 1
    
    def test_find_similar_stories(self, mock_embedding_service, mock_qdrant_client):
        """Test finding similar user stories."""
        # Setup mock response
        mock_search_result = [
            MagicMock(
                payload={
                    "story_id": "story-1",
                    "title": "Story 1",
                    "description": "Description 1"
                },
                score=0.95
            ),
            MagicMock(
                payload={
                    "story_id": "story-2",
                    "title": "Story 2",
                    "description": "Description 2"
                },
                score=0.85
            )
        ]
        mock_qdrant_client.search.return_value = mock_search_result
        
        store = QdrantVectorStore()
        results = store.find_similar_stories(SAMPLE_USER_STORY, limit=2)
        
        assert mock_qdrant_client.search.called
        search_args = mock_qdrant_client.search.call_args[1]
        assert search_args["collection_name"] == "user_stories"
        assert search_args["limit"] == 2
        
        assert len(results) == 2
        assert results[0]["story_id"] == "story-1"
        assert results[0]["similarity_score"] == 0.95
        assert results[1]["story_id"] == "story-2"
        assert results[1]["similarity_score"] == 0.85
    
    def test_find_similar_test_cases(self, mock_embedding_service, mock_qdrant_client):
        """Test finding similar test cases."""
        # Setup mock response
        mock_search_result = [
            MagicMock(
                payload={
                    "test_id": "test-1",
                    "title": "Test 1",
                    "description": "Description 1"
                },
                score=0.92
            )
        ]
        mock_qdrant_client.search.return_value = mock_search_result
        
        store = QdrantVectorStore()
        results = store.find_similar_test_cases(SAMPLE_USER_STORY, limit=1)
        
        assert mock_qdrant_client.search.called
        search_args = mock_qdrant_client.search.call_args[1]
        assert search_args["collection_name"] == "test_cases"
        assert search_args["limit"] == 1
        
        assert len(results) == 1
        assert results[0]["test_id"] == "test-1"
        assert results[0]["similarity_score"] == 0.92
    
    def test_health_check(self, mock_embedding_service, mock_qdrant_client):
        """Test the health check function."""
        store = QdrantVectorStore()
        
        # Test successful health check
        assert store.health_check() is True
        
        # Test failed health check
        mock_qdrant_client.get_collections.side_effect = Exception("Connection error")
        assert store.health_check() is False

class TestWeaviateVectorStore:
    """Tests for the WeaviateVectorStore class."""
    
    def test_init_creates_schema(self, mock_embedding_service, mock_weaviate_client):
        """Test that the constructor creates schema if it doesn't exist."""
        with patch("os.path.exists", return_value=False):
            store = WeaviateVectorStore()
            assert mock_weaviate_client.schema.create_class.called
    
    def test_store_user_story(self, mock_embedding_service, mock_weaviate_client):
        """Test storing a user story."""
        store = WeaviateVectorStore()
        result = store.store_user_story(SAMPLE_USER_STORY)
        
        assert result == SAMPLE_USER_STORY.story_id
        assert mock_weaviate_client.data_object.create.called
        create_args = mock_weaviate_client.data_object.create.call_args
        assert create_args[1] == "UserStory"  # class name
        properties = create_args[0]  # properties dict
        assert properties["story_id"] == SAMPLE_USER_STORY.story_id
        assert properties["title"] == SAMPLE_USER_STORY.title
    
    def test_store_test_case(self, mock_embedding_service, mock_weaviate_client):
        """Test storing a test case."""
        store = WeaviateVectorStore()
        result = store.store_test_case(SAMPLE_TEST_CASE)
        
        assert result == SAMPLE_TEST_CASE.test_id
        assert mock_weaviate_client.data_object.create.called
        create_args = mock_weaviate_client.data_object.create.call_args
        assert create_args[1] == "TestCase"  # class name
        properties = create_args[0]  # properties dict
        assert properties["test_id"] == SAMPLE_TEST_CASE.test_id
        assert properties["title"] == SAMPLE_TEST_CASE.title
    
    def test_find_similar_stories(self, mock_embedding_service, mock_weaviate_client):
        """Test finding similar user stories."""
        # Setup mock query
        mock_query = MagicMock()
        mock_query.get.return_value = mock_query
        mock_query.with_near_vector.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.with_additional.return_value = mock_query
        
        # Setup mock response
        mock_query.do.return_value = {
            "data": {
                "Get": {
                    "UserStory": [
                        {
                            "story_id": "story-1",
                            "project_id": "project-1",
                            "title": "Story 1",
                            "description": "Description 1",
                            "created_at": "2025-05-08T10:00:00Z",
                            "_additional": {"certainty": 0.95}
                        },
                        {
                            "story_id": "story-2",
                            "project_id": "project-2",
                            "title": "Story 2",
                            "description": "Description 2",
                            "created_at": "2025-05-08T11:00:00Z",
                            "_additional": {"certainty": 0.85}
                        }
                    ]
                }
            }
        }
        
        mock_weaviate_client.query = mock_query
        store = WeaviateVectorStore()
        results = store.find_similar_stories(SAMPLE_USER_STORY, limit=2)
        
        assert mock_query.get.called
        assert mock_query.with_near_vector.called
        assert mock_query.with_limit.called
        assert mock_query.do.called
        
        assert len(results) == 2
        assert results[0]["story_id"] == "story-1"
        assert results[0]["similarity_score"] == 0.95
        assert results[1]["story_id"] == "story-2"
        assert results[1]["similarity_score"] == 0.85
    
    def test_find_similar_test_cases(self, mock_embedding_service, mock_weaviate_client):
        """Test finding similar test cases."""
        # Setup mock query
        mock_query = MagicMock()
        mock_query.get.return_value = mock_query
        mock_query.with_near_vector.return_value = mock_query
        mock_query.with_limit.return_value = mock_query
        mock_query.with_additional.return_value = mock_query
        
        # Setup mock response
        mock_query.do.return_value = {
            "data": {
                "Get": {
                    "TestCase": [
                        {
                            "test_id": "test-1",
                            "story_id": "story-1",
                            "title": "Test 1",
                            "description": "Description 1",
                            "steps": '[{"step":"1","description":"Step 1"}]',
                            "expected_result": "Expected result 1",
                            "test_type": "positive",
                            "test_case_text": "Test case text 1",
                            "test_case_csv": "CSV 1",
                            "generated_at": "2025-05-08T10:00:00Z",
                            "_additional": {"certainty": 0.92}
                        }
                    ]
                }
            }
        }
        
        mock_weaviate_client.query = mock_query
        store = WeaviateVectorStore()
        results = store.find_similar_test_cases(SAMPLE_USER_STORY, limit=1)
        
        assert mock_query.get.called
        assert mock_query.with_near_vector.called
        assert mock_query.with_limit.called
        assert mock_query.do.called
        
        assert len(results) == 1
        assert results[0]["test_id"] == "test-1"
        assert results[0]["similarity_score"] == 0.92
        assert isinstance(results[0]["steps"], list)
    
    def test_health_check(self, mock_embedding_service, mock_weaviate_client):
        """Test the health check function."""
        store = WeaviateVectorStore()
        
        # Test successful health check
        assert store.health_check() is True
        
        # Test failed health check
        mock_weaviate_client.schema.get.side_effect = Exception("Connection error")
        assert store.health_check() is False

def test_get_vector_store():
    """Test getting the appropriate vector store service."""
    # Test Qdrant
    with patch("app.services.vector_store.VECTOR_DB_TYPE", "qdrant"):
        with patch("app.services.vector_store.QdrantVectorStore") as mock_qdrant:
            store = get_vector_store()
            assert mock_qdrant.called
    
    # Test Weaviate
    with patch("app.services.vector_store.VECTOR_DB_TYPE", "weaviate"):
        with patch("app.services.vector_store.WeaviateVectorStore") as mock_weaviate:
            store = get_vector_store()
            assert mock_weaviate.called
    
    # Test unsupported
    with patch("app.services.vector_store.VECTOR_DB_TYPE", "unsupported"):
        with pytest.raises(ValueError):
            store = get_vector_store()
