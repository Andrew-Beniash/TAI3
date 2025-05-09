"""
Vector store service.
Handles storage and retrieval of user stories and test cases in a vector database.
"""
import logging
from typing import List, Dict, Any, Optional, Union
import json
import os
import uuid

from app.config import get_vector_db_credentials, VECTOR_DB_TYPE
from app.models.data_models import UserStoryRecord, TestCaseRecord, VectorSearchResult

# Configure logging
logger = logging.getLogger(__name__)

# Initialize vector DB client
vector_db_client = None
vector_db_config = get_vector_db_credentials()

# Try to initialize the appropriate vector DB client
try:
    if vector_db_config["type"].lower() == "weaviate":
        try:
            import weaviate
            from weaviate.auth import AuthApiKey
            
            # Initialize Weaviate client
            auth_config = AuthApiKey(api_key=vector_db_config["api_key"]) if vector_db_config["api_key"] else None
            vector_db_client = weaviate.Client(
                url=vector_db_config["url"],
                auth_client_secret=auth_config
            )
            logger.info("Weaviate client initialized successfully")
        except ImportError:
            logger.error("Weaviate package not installed. Please install with 'pip install weaviate-client'")
        except Exception as e:
            logger.error(f"Error initializing Weaviate client: {e}", exc_info=True)
            
    elif vector_db_config["type"].lower() == "qdrant":
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            
            # Initialize Qdrant client
            vector_db_client = QdrantClient(
                url=vector_db_config["url"],
                api_key=vector_db_config["api_key"] if vector_db_config["api_key"] else None
            )
            logger.info("Qdrant client initialized successfully")
        except ImportError:
            logger.error("Qdrant package not installed. Please install with 'pip install qdrant-client'")
        except Exception as e:
            logger.error(f"Error initializing Qdrant client: {e}", exc_info=True)
    
    elif vector_db_config["type"].lower() == "faiss":
        try:
            import faiss
            import numpy as np
            
            # Initialize FAISS index (in-memory for now)
            # This is a simplified implementation for demo purposes
            vector_db_client = {
                "dimension": 1536,  # Default dimension for OpenAI embeddings
                "index": None,  # Will be initialized when first used
                "user_stories": {},
                "test_cases": {}
            }
            logger.info("FAISS in-memory store initialized successfully")
        except ImportError:
            logger.error("FAISS package not installed. Please install with 'pip install faiss-cpu'")
        except Exception as e:
            logger.error(f"Error initializing FAISS: {e}", exc_info=True)
    
    else:
        logger.error(f"Unsupported vector DB type: {vector_db_config['type']}")

except Exception as e:
    logger.error(f"Error initializing vector store: {e}", exc_info=True)

# Helper function to create schema if needed
async def ensure_schema_exists():
    """
    Ensure that the necessary schema/collections exist in the vector DB.
    This is called on startup or when first needed.
    """
    if vector_db_client is None:
        logger.error("Vector DB client not initialized")
        return False
        
    try:
        if vector_db_config["type"].lower() == "weaviate":
            # Check if classes exist, create them if they don't
            schema = vector_db_client.schema.get()
            
            # Create UserStory class if it doesn't exist
            if not any(cls["class"] == "UserStory" for cls in schema["classes"]):
                class_obj = {
                    "class": "UserStory",
                    "description": "User story from Azure DevOps",
                    "vectorizer": "none",  # We provide embeddings directly
                    "properties": [
                        {"name": "story_id", "dataType": ["string"]},
                        {"name": "project_id", "dataType": ["string"]},
                        {"name": "title", "dataType": ["text"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "created_at", "dataType": ["date"]}
                    ]
                }
                vector_db_client.schema.create_class(class_obj)
                logger.info("Created UserStory class in Weaviate")
                
            # Create TestCase class if it doesn't exist
            if not any(cls["class"] == "TestCase" for cls in schema["classes"]):
                class_obj = {
                    "class": "TestCase",
                    "description": "Test case generated for a user story",
                    "vectorizer": "none",  # We provide embeddings directly
                    "properties": [
                        {"name": "story_id", "dataType": ["string"]},
                        {"name": "test_case_id", "dataType": ["string"]},
                        {"name": "title", "dataType": ["text"]},
                        {"name": "description", "dataType": ["text"]},
                        {"name": "test_case_text", "dataType": ["text"]},
                        {"name": "test_case_csv", "dataType": ["text"]},
                        {"name": "steps", "dataType": ["text[]"]},
                        {"name": "generated_at", "dataType": ["date"]}
                    ]
                }
                vector_db_client.schema.create_class(class_obj)
                logger.info("Created TestCase class in Weaviate")
                
        elif vector_db_config["type"].lower() == "qdrant":
            from qdrant_client.http import models
            
            # Create user_stories collection if it doesn't exist
            collections = vector_db_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if "user_stories" not in collection_names:
                vector_db_client.create_collection(
                    collection_name="user_stories",
                    vectors_config=models.VectorParams(
                        size=1536,  # Default for OpenAI embeddings
                        distance=models.Distance.COSINE
                    )
                )
                logger.info("Created user_stories collection in Qdrant")
                
            if "test_cases" not in collection_names:
                vector_db_client.create_collection(
                    collection_name="test_cases",
                    vectors_config=models.VectorParams(
                        size=1536,  # Default for OpenAI embeddings
                        distance=models.Distance.COSINE
                    )
                )
                logger.info("Created test_cases collection in Qdrant")
                
        elif vector_db_config["type"].lower() == "faiss":
            # For FAISS, we'll just initialize the index if it doesn't exist
            if vector_db_client["index"] is None:
                import faiss
                vector_db_client["index"] = {
                    "user_stories": faiss.IndexFlatL2(vector_db_client["dimension"]),
                    "test_cases": faiss.IndexFlatL2(vector_db_client["dimension"])
                }
                logger.info("Initialized FAISS indices")
                
        return True
    except Exception as e:
        logger.error(f"Error ensuring schema exists: {e}", exc_info=True)
        return False

# Store a user story in the vector DB
async def store_user_story(story: UserStoryRecord) -> bool:
    """
    Store a user story in the vector database.
    
    Args:
        story: The user story to store
        
    Returns:
        bool: True if successful, False otherwise
    """
    if vector_db_client is None:
        logger.error("Vector DB client not initialized")
        return False
        
    if not story.embedding:
        logger.error("User story embedding is missing")
        return False
        
    try:
        # Ensure schema exists
        await ensure_schema_exists()
        
        if vector_db_config["type"].lower() == "weaviate":
            # Convert to Weaviate format
            story_dict = story.dict()
            
            # Extract the embedding
            embedding = story_dict.pop("embedding")
            
            # Add the story to Weaviate
            vector_db_client.data_object.create(
                class_name="UserStory",
                data_object=story_dict,
                vector=embedding
            )
            logger.info(f"Stored user story {story.story_id} in Weaviate")
            
        elif vector_db_config["type"].lower() == "qdrant":
            from qdrant_client.http import models
            
            # Add the story to Qdrant
            vector_db_client.upsert(
                collection_name="user_stories",
                points=[
                    models.PointStruct(
                        id=story.story_id,
                        vector=story.embedding,
                        payload=story.dict(exclude={"embedding"})
                    )
                ]
            )
            logger.info(f"Stored user story {story.story_id} in Qdrant")
            
        elif vector_db_config["type"].lower() == "faiss":
            import numpy as np
            
            # Convert embedding to numpy array
            embedding_np = np.array([story.embedding], dtype=np.float32)
            
            # Add to FAISS index
            index = vector_db_client["index"]["user_stories"]
            index.add(embedding_np)
            
            # Store the story data (excluding embedding)
            story_id = story.story_id
            vector_db_client["user_stories"][story_id] = story.dict(exclude={"embedding"})
            
            logger.info(f"Stored user story {story.story_id} in FAISS")
            
        return True
    except Exception as e:
        logger.error(f"Error storing user story: {e}", exc_info=True)
        return False

# Store test cases in the vector DB
async def store_test_cases(test_cases: List[TestCaseRecord]) -> bool:
    """
    Store test cases in the vector database.
    
    Args:
        test_cases: List of test cases to store
        
    Returns:
        bool: True if successful, False otherwise
    """
    if vector_db_client is None:
        logger.error("Vector DB client not initialized")
        return False
        
    if not test_cases:
        logger.warning("No test cases to store")
        return True
        
    try:
        # Ensure schema exists
        await ensure_schema_exists()
        
        if vector_db_config["type"].lower() == "weaviate":
            for test_case in test_cases:
                # Skip if embedding is missing
                if not test_case.embedding:
                    logger.warning(f"Test case {test_case.title} has no embedding, skipping")
                    continue
                    
                # Convert to Weaviate format
                test_case_dict = test_case.dict()
                
                # Convert steps to list of strings for Weaviate
                if "steps" in test_case_dict and test_case_dict["steps"]:
                    test_case_dict["steps"] = [json.dumps(step) for step in test_case_dict["steps"]]
                
                # Extract the embedding
                embedding = test_case_dict.pop("embedding")
                
                # Add the test case to Weaviate
                vector_db_client.data_object.create(
                    class_name="TestCase",
                    data_object=test_case_dict,
                    vector=embedding
                )
                logger.info(f"Stored test case '{test_case.title}' in Weaviate")
            
        elif vector_db_config["type"].lower() == "qdrant":
            from qdrant_client.http import models
            
            points = []
            for test_case in test_cases:
                # Skip if embedding is missing
                if not test_case.embedding:
                    logger.warning(f"Test case {test_case.title} has no embedding, skipping")
                    continue
                
                # Generate a unique ID if test_case_id is not provided
                test_case_id = test_case.test_case_id or f"tc-{uuid.uuid4()}"
                
                points.append(
                    models.PointStruct(
                        id=test_case_id,
                        vector=test_case.embedding,
                        payload=test_case.dict(exclude={"embedding"})
                    )
                )
            
            if points:
                vector_db_client.upsert(
                    collection_name="test_cases",
                    points=points
                )
                logger.info(f"Stored {len(points)} test cases in Qdrant")
            
        elif vector_db_config["type"].lower() == "faiss":
            import numpy as np
            
            # Collect embeddings for FAISS
            embeddings = []
            for i, test_case in enumerate(test_cases):
                # Skip if embedding is missing
                if not test_case.embedding:
                    logger.warning(f"Test case {test_case.title} has no embedding, skipping")
                    continue
                    
                # Add embedding to list
                embeddings.append(test_case.embedding)
                
                # Generate a unique ID if test_case_id is not provided
                test_case_id = test_case.test_case_id or f"tc-{uuid.uuid4()}"
                
                # Store the test case data (excluding embedding)
                vector_db_client["test_cases"][test_case_id] = test_case.dict(exclude={"embedding"})
            
            if embeddings:
                # Convert embeddings to numpy array
                embeddings_np = np.array(embeddings, dtype=np.float32)
                
                # Add to FAISS index
                index = vector_db_client["index"]["test_cases"]
                index.add(embeddings_np)
                
                logger.info(f"Stored {len(embeddings)} test cases in FAISS")
            
        return True
    except Exception as e:
        logger.error(f"Error storing test cases: {e}", exc_info=True)
        return False

# Search for similar user stories
async def search_similar_user_stories(
    embedding: List[float], 
    limit: int = 3
) -> List[UserStoryRecord]:
    """
    Search for similar user stories in the vector database.
    
    Args:
        embedding: The query embedding
        limit: Maximum number of results to return
        
    Returns:
        List[UserStoryRecord]: List of similar user stories
    """
    if vector_db_client is None:
        logger.error("Vector DB client not initialized")
        return []
        
    if not embedding:
        logger.error("Query embedding is missing")
        return []
        
    try:
        # Ensure schema exists
        await ensure_schema_exists()
        
        if vector_db_config["type"].lower() == "weaviate":
            import weaviate.classes as wvc
            
            # Search for similar user stories
            query = (
                vector_db_client.query
                .get("UserStory", ["story_id", "project_id", "title", "description", "created_at"])
                .with_near_vector({
                    "vector": embedding,
                })
                .with_limit(limit)
            )
            
            # Execute the query
            result = query.do()
            
            # Convert to UserStoryRecord objects
            user_stories = []
            for item in result.get("data", {}).get("Get", {}).get("UserStory", []):
                user_stories.append(UserStoryRecord(**item))
                
            logger.info(f"Found {len(user_stories)} similar user stories in Weaviate")
            return user_stories
            
        elif vector_db_config["type"].lower() == "qdrant":
            from qdrant_client.http import models
            
            # Search for similar user stories
            search_result = vector_db_client.search(
                collection_name="user_stories",
                query_vector=embedding,
                limit=limit
            )
            
            # Convert to UserStoryRecord objects
            user_stories = []
            for item in search_result:
                user_story_data = item.payload
                user_story_data["embedding"] = None  # Embedding is not returned by Qdrant
                user_stories.append(UserStoryRecord(**user_story_data))
                
            logger.info(f"Found {len(user_stories)} similar user stories in Qdrant")
            return user_stories
            
        elif vector_db_config["type"].lower() == "faiss":
            import numpy as np
            
            # Convert query to numpy array
            query_vector = np.array([embedding], dtype=np.float32)
            
            # Search the index
            index = vector_db_client["index"]["user_stories"]
            D, I = index.search(query_vector, limit)
            
            # Convert indices to user story objects
            user_stories = []
            for i in range(I.shape[1]):
                idx = I[0, i]
                if idx >= 0 and idx < len(vector_db_client["user_stories"]):
                    # Get the story ID at this index
                    story_id = list(vector_db_client["user_stories"].keys())[idx]
                    story_data = vector_db_client["user_stories"][story_id]
                    user_stories.append(UserStoryRecord(**story_data))
                
            logger.info(f"Found {len(user_stories)} similar user stories in FAISS")
            return user_stories
            
        return []
    except Exception as e:
        logger.error(f"Error searching for similar user stories: {e}", exc_info=True)
        return []

# Search for similar test cases
async def search_similar_test_cases(
    embedding: List[float], 
    limit: int = 5
) -> List[TestCaseRecord]:
    """
    Search for similar test cases in the vector database.
    
    Args:
        embedding: The query embedding
        limit: Maximum number of results to return
        
    Returns:
        List[TestCaseRecord]: List of similar test cases
    """
    if vector_db_client is None:
        logger.error("Vector DB client not initialized")
        return []
        
    if not embedding:
        logger.error("Query embedding is missing")
        return []
        
    try:
        # Ensure schema exists
        await ensure_schema_exists()
        
        if vector_db_config["type"].lower() == "weaviate":
            import weaviate.classes as wvc
            
            # Search for similar test cases
            query = (
                vector_db_client.query
                .get("TestCase", ["story_id", "test_case_id", "title", "description", "test_case_text", "test_case_csv", "steps", "generated_at"])
                .with_near_vector({
                    "vector": embedding,
                })
                .with_limit(limit)
            )
            
            # Execute the query
            result = query.do()
            
            # Convert to TestCaseRecord objects
            test_cases = []
            for item in result.get("data", {}).get("Get", {}).get("TestCase", []):
                # Convert steps from JSON strings back to dictionaries
                if "steps" in item and item["steps"]:
                    item["steps"] = [json.loads(step) for step in item["steps"]]
                    
                test_cases.append(TestCaseRecord(**item))
                
            logger.info(f"Found {len(test_cases)} similar test cases in Weaviate")
            return test_cases
            
        elif vector_db_config["type"].lower() == "qdrant":
            from qdrant_client.http import models
            
            # Search for similar test cases
            search_result = vector_db_client.search(
                collection_name="test_cases",
                query_vector=embedding,
                limit=limit
            )
            
            # Convert to TestCaseRecord objects
            test_cases = []
            for item in search_result:
                test_case_data = item.payload
                test_case_data["embedding"] = None  # Embedding is not returned by Qdrant
                test_cases.append(TestCaseRecord(**test_case_data))
                
            logger.info(f"Found {len(test_cases)} similar test cases in Qdrant")
            return test_cases
            
        elif vector_db_config["type"].lower() == "faiss":
            import numpy as np
            
            # Convert query to numpy array
            query_vector = np.array([embedding], dtype=np.float32)
            
            # Search the index
            index = vector_db_client["index"]["test_cases"]
            D, I = index.search(query_vector, limit)
            
            # Convert indices to test case objects
            test_cases = []
            for i in range(I.shape[1]):
                idx = I[0, i]
                if idx >= 0 and idx < len(vector_db_client["test_cases"]):
                    # Get the test case ID at this index
                    test_case_id = list(vector_db_client["test_cases"].keys())[idx]
                    test_case_data = vector_db_client["test_cases"][test_case_id]
                    test_cases.append(TestCaseRecord(**test_case_data))
                
            logger.info(f"Found {len(test_cases)} similar test cases in FAISS")
            return test_cases
            
        return []
    except Exception as e:
        logger.error(f"Error searching for similar test cases: {e}", exc_info=True)
        return []
