"""
Vector store service for the QA Agent application.
Provides an abstraction layer for different vector databases.
"""
import logging
import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
import weaviate
from weaviate.util import generate_uuid5

from app.config import (
    VECTOR_DB_TYPE, QDRANT_URL, WEAVIATE_URL,
    USER_STORIES_COLLECTION, TEST_CASES_COLLECTION,
    EMBEDDING_DIMENSIONS
)
from app.models.data_models import UserStory, TestCase
from app.services.embedding import get_embedding_service

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Abstract base class for vector store services."""
    
    def __init__(self):
        """Initialize the vector store service."""
        self.embedding_service = get_embedding_service()
        
    def store_user_story(self, user_story: UserStory) -> str:
        """Store a user story in the vector store."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def store_test_case(self, test_case: TestCase) -> str:
        """Store a test case in the vector store."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def find_similar_stories(self, user_story: UserStory, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar user stories in the vector store."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def find_similar_test_cases(self, user_story: UserStory, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar test cases in the vector store."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def health_check(self) -> bool:
        """Check if the vector store is healthy."""
        raise NotImplementedError("Subclasses must implement this method")

class QdrantVectorStore(VectorStoreService):
    """Vector store service using Qdrant."""
    
    def __init__(self):
        """Initialize the Qdrant vector store service."""
        super().__init__()
        self.client = QdrantClient(url=QDRANT_URL)
        self._ensure_collections_exist()
    
    def _ensure_collections_exist(self):
        """Ensure that the required collections exist in Qdrant."""
        try:
            # Check if user stories collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if USER_STORIES_COLLECTION not in collection_names:
                logger.info(f"Creating collection {USER_STORIES_COLLECTION}")
                self.client.create_collection(
                    collection_name=USER_STORIES_COLLECTION,
                    vectors_config=qdrant_models.VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
            
            if TEST_CASES_COLLECTION not in collection_names:
                logger.info(f"Creating collection {TEST_CASES_COLLECTION}")
                self.client.create_collection(
                    collection_name=TEST_CASES_COLLECTION,
                    vectors_config=qdrant_models.VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error creating Qdrant collections: {e}")
            raise
    
    def store_user_story(self, user_story: UserStory) -> str:
        """Store a user story in Qdrant."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        payload = {
            "story_id": user_story.story_id,
            "project_id": user_story.project_id,
            "title": user_story.title,
            "description": user_story.description,
            "created_at": user_story.created_at.isoformat()
        }
        
        self.client.upsert(
            collection_name=USER_STORIES_COLLECTION,
            points=[
                qdrant_models.PointStruct(
                    id=user_story.story_id,
                    vector=user_story.embedding,
                    payload=payload
                )
            ]
        )
        
        return user_story.story_id
    
    def store_test_case(self, test_case: TestCase) -> str:
        """Store a test case in Qdrant."""
        if not test_case.test_id:
            test_case.test_id = str(uuid.uuid4())
            
        if not test_case.embedding:
            steps_text = "\n".join([f"{step['step']}. {step['description']}" for step in test_case.steps])
            test_case.embedding = self.embedding_service.embed_test_case(
                test_case.title, test_case.description, steps_text, test_case.expected_result
            )
        
        payload = {
            "test_id": test_case.test_id,
            "story_id": test_case.story_id,
            "title": test_case.title,
            "description": test_case.description,
            "steps": test_case.steps,
            "expected_result": test_case.expected_result,
            "test_type": test_case.test_type,
            "test_case_text": test_case.test_case_text,
            "test_case_csv": test_case.test_case_csv,
            "generated_at": test_case.generated_at.isoformat()
        }
        
        self.client.upsert(
            collection_name=TEST_CASES_COLLECTION,
            points=[
                qdrant_models.PointStruct(
                    id=test_case.test_id,
                    vector=test_case.embedding,
                    payload=payload
                )
            ]
        )
        
        return test_case.test_id
    
    def find_similar_stories(self, user_story: UserStory, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar user stories in Qdrant."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        search_result = self.client.search(
            collection_name=USER_STORIES_COLLECTION,
            query_vector=user_story.embedding,
            limit=limit
        )
        
        results = []
        for result in search_result:
            payload = result.payload
            payload["similarity_score"] = result.score
            results.append(payload)
        
        return results
    
    def find_similar_test_cases(self, user_story: UserStory, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar test cases in Qdrant."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        search_result = self.client.search(
            collection_name=TEST_CASES_COLLECTION,
            query_vector=user_story.embedding,
            limit=limit
        )
        
        results = []
        for result in search_result:
            payload = result.payload
            payload["similarity_score"] = result.score
            results.append(payload)
        
        return results
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

class WeaviateVectorStore(VectorStoreService):
    """Vector store service using Weaviate."""
    
    def __init__(self):
        """Initialize the Weaviate vector store service."""
        super().__init__()
        self.client = weaviate.Client(url=WEAVIATE_URL)
        self._ensure_schema_exists()
    
    def _ensure_schema_exists(self):
        """Ensure that the required schema exists in Weaviate."""
        try:
            schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     "vector_db", "schema.yaml")
            
            # Check if schema classes exist
            schema = self.client.schema.get()
            existing_classes = [cls['class'] for cls in schema.get('classes', [])]
            
            # If both classes already exist, return
            if "UserStory" in existing_classes and "TestCase" in existing_classes:
                logger.info("Weaviate schema already exists")
                return
            
            # Load schema from YAML file
            if os.path.exists(schema_path):
                # If you're using PyYAML, you could do this:
                import yaml
                with open(schema_path, 'r') as f:
                    schema_config = yaml.safe_load(f)
                
                # Create schema classes
                for class_def in schema_config.get('classes', []):
                    if class_def['class'] not in existing_classes:
                        logger.info(f"Creating Weaviate class: {class_def['class']}")
                        self.client.schema.create_class(class_def)
            else:
                # Create schema manually if YAML file doesn't exist
                self._create_default_schema()
                
        except Exception as e:
            logger.error(f"Error creating Weaviate schema: {e}")
            raise
    
    def _create_default_schema(self):
        """Create default schema if schema file doesn't exist."""
        # UserStory class
        if not self.client.schema.exists("UserStory"):
            user_story_class = {
                "class": "UserStory",
                "description": "User story from Azure DevOps",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "story_id",
                        "dataType": ["string"],
                        "description": "Unique ID of the user story",
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "field"
                    },
                    {
                        "name": "project_id",
                        "dataType": ["string"],
                        "description": "ID of the project",
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "field"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Title of the user story",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "description",
                        "dataType": ["text"],
                        "description": "Description of the user story",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "created_at",
                        "dataType": ["date"],
                        "description": "Creation timestamp",
                        "indexFilterable": True,
                        "indexSearchable": True
                    }
                ]
            }
            self.client.schema.create_class(user_story_class)
            logger.info("Created UserStory class in Weaviate")
        
        # TestCase class
        if not self.client.schema.exists("TestCase"):
            test_case_class = {
                "class": "TestCase",
                "description": "Test case generated for a user story",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "test_id",
                        "dataType": ["string"],
                        "description": "Unique ID of the test case",
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "field"
                    },
                    {
                        "name": "story_id",
                        "dataType": ["string"],
                        "description": "ID of the user story this test case is for",
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "field"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Title of the test case",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "description",
                        "dataType": ["text"],
                        "description": "Description of the test case",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "steps",
                        "dataType": ["string"],
                        "description": "JSON string of test case steps",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "expected_result",
                        "dataType": ["text"],
                        "description": "Expected result of the test case",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "test_type",
                        "dataType": ["string"],
                        "description": "Type of test (positive, negative, edge)",
                        "indexFilterable": True,
                        "indexSearchable": True,
                        "tokenization": "field"
                    },
                    {
                        "name": "test_case_text",
                        "dataType": ["text"],
                        "description": "Full test case in text/markdown format",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "test_case_csv",
                        "dataType": ["text"],
                        "description": "Test case in CSV format",
                        "indexFilterable": True,
                        "indexSearchable": True
                    },
                    {
                        "name": "generated_at",
                        "dataType": ["date"],
                        "description": "Generation timestamp",
                        "indexFilterable": True,
                        "indexSearchable": True
                    }
                ]
            }
            self.client.schema.create_class(test_case_class)
            logger.info("Created TestCase class in Weaviate")
    
    def store_user_story(self, user_story: UserStory) -> str:
        """Store a user story in Weaviate."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        # Generate a UUID based on the story_id to ensure idempotency
        uuid_id = generate_uuid5(user_story.story_id)
        
        # Properties to store
        properties = {
            "story_id": user_story.story_id,
            "project_id": user_story.project_id,
            "title": user_story.title,
            "description": user_story.description,
            "created_at": user_story.created_at.isoformat()
        }
        
        # Store the object with its vector
        try:
            self.client.data_object.create(
                properties,
                "UserStory",
                uuid_id,
                vector=user_story.embedding
            )
            logger.info(f"Stored user story {user_story.story_id} in Weaviate")
            return user_story.story_id
        except Exception as e:
            logger.error(f"Error storing user story in Weaviate: {e}")
            raise
    
    def store_test_case(self, test_case: TestCase) -> str:
        """Store a test case in Weaviate."""
        if not test_case.test_id:
            test_case.test_id = str(uuid.uuid4())
            
        if not test_case.embedding:
            steps_text = "\n".join([f"{step['step']}. {step['description']}" for step in test_case.steps])
            test_case.embedding = self.embedding_service.embed_test_case(
                test_case.title, test_case.description, steps_text, test_case.expected_result
            )
        
        # Generate a UUID based on the test_id to ensure idempotency
        uuid_id = generate_uuid5(test_case.test_id)
        
        # Convert steps to JSON string for storage
        steps_json = json.dumps(test_case.steps)
        
        # Properties to store
        properties = {
            "test_id": test_case.test_id,
            "story_id": test_case.story_id,
            "title": test_case.title,
            "description": test_case.description,
            "steps": steps_json,
            "expected_result": test_case.expected_result,
            "test_type": test_case.test_type,
            "test_case_text": test_case.test_case_text,
            "test_case_csv": test_case.test_case_csv,
            "generated_at": test_case.generated_at.isoformat()
        }
        
        # Store the object with its vector
        try:
            self.client.data_object.create(
                properties,
                "TestCase",
                uuid_id,
                vector=test_case.embedding
            )
            logger.info(f"Stored test case {test_case.test_id} in Weaviate")
            return test_case.test_id
        except Exception as e:
            logger.error(f"Error storing test case in Weaviate: {e}")
            raise
    
    def find_similar_stories(self, user_story: UserStory, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar user stories in Weaviate."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        try:
            # Define the query to find similar user stories
            query = (
                self.client.query
                .get("UserStory", [
                    "story_id", "project_id", "title", "description", "created_at"
                ])
                .with_near_vector({
                    "vector": user_story.embedding
                })
                .with_limit(limit)
                .with_additional(["certainty", "id"])
            )
            
            # Execute the query
            result = query.do()
            
            # Process the results
            if "data" in result and "Get" in result["data"] and "UserStory" in result["data"]["Get"]:
                stories = result["data"]["Get"]["UserStory"]
                processed_results = []
                
                for story in stories:
                    # Skip if the story_id is the same as the input story
                    if story["story_id"] == user_story.story_id:
                        continue
                    
                    # Extract certainty score
                    certainty = story.get("_additional", {}).get("certainty", 0)
                    
                    # Add similarity score to the result
                    story_result = {
                        "story_id": story["story_id"],
                        "project_id": story["project_id"],
                        "title": story["title"],
                        "description": story["description"],
                        "created_at": story["created_at"],
                        "similarity_score": certainty
                    }
                    processed_results.append(story_result)
                
                return processed_results
            else:
                logger.warning("No similar user stories found in Weaviate")
                return []
        except Exception as e:
            logger.error(f"Error finding similar user stories in Weaviate: {e}")
            return []
    
    def find_similar_test_cases(self, user_story: UserStory, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar test cases in Weaviate."""
        if not user_story.embedding:
            user_story.embedding = self.embedding_service.embed_user_story(
                user_story.title, user_story.description
            )
        
        try:
            # Define the query to find similar test cases
            query = (
                self.client.query
                .get("TestCase", [
                    "test_id", "story_id", "title", "description", 
                    "steps", "expected_result", "test_type", 
                    "test_case_text", "test_case_csv", "generated_at"
                ])
                .with_near_vector({
                    "vector": user_story.embedding
                })
                .with_limit(limit)
                .with_additional(["certainty", "id"])
            )
            
            # Execute the query
            result = query.do()
            
            # Process the results
            if "data" in result and "Get" in result["data"] and "TestCase" in result["data"]["Get"]:
                test_cases = result["data"]["Get"]["TestCase"]
                processed_results = []
                
                for test_case in test_cases:
                    # Extract certainty score
                    certainty = test_case.get("_additional", {}).get("certainty", 0)
                    
                    # Parse steps back to list
                    steps = json.loads(test_case["steps"]) if isinstance(test_case["steps"], str) else test_case["steps"]
                    
                    # Add similarity score to the result
                    test_case_result = {
                        "test_id": test_case["test_id"],
                        "story_id": test_case["story_id"],
                        "title": test_case["title"],
                        "description": test_case["description"],
                        "steps": steps,
                        "expected_result": test_case["expected_result"],
                        "test_type": test_case["test_type"],
                        "test_case_text": test_case["test_case_text"],
                        "test_case_csv": test_case["test_case_csv"],
                        "generated_at": test_case["generated_at"],
                        "similarity_score": certainty
                    }
                    processed_results.append(test_case_result)
                
                return processed_results
            else:
                logger.warning("No similar test cases found in Weaviate")
                return []
        except Exception as e:
            logger.error(f"Error finding similar test cases in Weaviate: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        try:
            self.client.schema.get()
            return True
        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return False

def get_vector_store() -> VectorStoreService:
    """Get the appropriate vector store service based on configuration."""
    if VECTOR_DB_TYPE.lower() == "qdrant":
        return QdrantVectorStore()
    elif VECTOR_DB_TYPE.lower() == "weaviate":
        return WeaviateVectorStore()
    else:
        raise ValueError(f"Unsupported vector store type: {VECTOR_DB_TYPE}")
