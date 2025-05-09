"""
Script to test the connection to the vector database.
"""
import sys
import os
from pathlib import Path
import argparse
import json

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import application components
from app.config import get_vector_db_credentials, validate_config
from dotenv import load_dotenv

def test_weaviate_connection(url, api_key=None):
    """Test connection to Weaviate"""
    try:
        import weaviate
        from weaviate.auth import AuthApiKey
        
        print(f"Connecting to Weaviate at {url}...")
        
        # Setup authentication if provided
        auth_config = AuthApiKey(api_key=api_key) if api_key else None
        
        # Create client
        client = weaviate.Client(
            url=url,
            auth_client_secret=auth_config
        )
        
        # Check connection
        metadata = client.get_meta()
        
        print("Connection successful!")
        print(f"Weaviate version: {metadata['version']}")
        
        # Get schema
        schema = client.schema.get()
        
        # Print classes
        print("\nAvailable classes:")
        if 'classes' in schema and schema['classes']:
            for cls in schema['classes']:
                print(f"- {cls['class']}")
        else:
            print("No classes found in schema.")
        
        return True
    except ImportError:
        print("Error: Weaviate client not installed.")
        print("Install with: pip install weaviate-client")
        return False
    except Exception as e:
        print(f"Error connecting to Weaviate: {str(e)}")
        return False

def test_qdrant_connection(url, api_key=None):
    """Test connection to Qdrant"""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        
        print(f"Connecting to Qdrant at {url}...")
        
        # Create client
        client = QdrantClient(
            url=url,
            api_key=api_key
        )
        
        # Check connection
        collections = client.get_collections()
        
        print("Connection successful!")
        
        # Print collections
        print("\nAvailable collections:")
        if collections.collections:
            for collection in collections.collections:
                print(f"- {collection.name}")
        else:
            print("No collections found.")
        
        return True
    except ImportError:
        print("Error: Qdrant client not installed.")
        print("Install with: pip install qdrant-client")
        return False
    except Exception as e:
        print(f"Error connecting to Qdrant: {str(e)}")
        return False

def test_faiss_connection():
    """Test FAISS setup"""
    try:
        import faiss
        import numpy as np
        
        print("Testing FAISS setup...")
        
        # Create a small index
        dimension = 1536
        index = faiss.IndexFlatL2(dimension)
        
        # Add some vectors
        vectors = np.random.random((10, dimension)).astype('float32')
        index.add(vectors)
        
        # Check if the index is working
        query = np.random.random((1, dimension)).astype('float32')
        D, I = index.search(query, 3)
        
        print("FAISS setup is working correctly!")
        print(f"Created index with dimension {dimension}")
        print(f"Added {index.ntotal} vectors")
        print(f"Search test returned {len(I[0])} results")
        
        return True
    except ImportError:
        print("Error: FAISS not installed.")
        print("Install with: pip install faiss-cpu or faiss-gpu")
        return False
    except Exception as e:
        print(f"Error testing FAISS: {str(e)}")
        return False

def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test vector database connection")
    parser.add_argument("--db-type", choices=["weaviate", "qdrant", "faiss"], 
                        help="Vector database type (default: from .env)")
    parser.add_argument("--url", help="Vector database URL (default: from .env)")
    parser.add_argument("--api-key", help="Vector database API key (default: from .env)")
    args = parser.parse_args()
    
    # Get configuration from .env or command-line args
    config = get_vector_db_credentials()
    
    db_type = args.db_type or config["type"]
    url = args.url or config["url"]
    api_key = args.api_key or config["api_key"]
    
    print(f"Testing connection to {db_type} vector database")
    
    if db_type.lower() == "weaviate":
        success = test_weaviate_connection(url, api_key)
    elif db_type.lower() == "qdrant":
        success = test_qdrant_connection(url, api_key)
    elif db_type.lower() == "faiss":
        success = test_faiss_connection()
    else:
        print(f"Error: Unsupported vector database type: {db_type}")
        success = False
    
    if success:
        print("\nVector database connection test completed successfully!")
        return 0
    else:
        print("\nVector database connection test failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
