#!/usr/bin/env python3
"""
Utility script to test the vector database functionality.
This script allows you to test the vector database independently by:
1. Storing sample user stories and test cases
2. Retrieving similar user stories and test cases
3. Testing the health check functionality

Usage:
    python test_vector_db.py --db-type [weaviate|qdrant] --action [store|retrieve|health]
"""
import os
import sys
import argparse
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to sys.path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.data_models import UserStory, TestCase
from app.services.vector_store import get_vector_store
from app.config import VECTOR_DB_TYPE

# Create sample user stories
SAMPLE_USER_STORIES = [
    UserStory(
        story_id=f"story-{uuid.uuid4()}",
        project_id="test-project",
        title="User can reset password",
        description="As a user, I want to be able to reset my password if I forget it so I can regain access to my account.",
        created_at=datetime.now()
    ),
    UserStory(
        story_id=f"story-{uuid.uuid4()}",
        project_id="test-project",
        title="User can update profile information",
        description="As a user, I want to be able to update my profile information so I can keep my details current.",
        created_at=datetime.now()
    ),
    UserStory(
        story_id=f"story-{uuid.uuid4()}",
        project_id="test-project",
        title="User can view order history",
        description="As a user, I want to be able to view my order history so I can track my past purchases.",
        created_at=datetime.now()
    ),
    UserStory(
        story_id=f"story-{uuid.uuid4()}",
        project_id="test-project",
        title="User can add items to cart",
        description="As a user, I want to be able to add items to my shopping cart so I can purchase them later.",
        created_at=datetime.now()
    ),
    UserStory(
        story_id=f"story-{uuid.uuid4()}",
        project_id="test-project",
        title="User can checkout and pay",
        description="As a user, I want to be able to checkout and pay for items in my cart so I can complete my purchase.",
        created_at=datetime.now()
    )
]

# Create sample test cases for the first user story
SAMPLE_TEST_CASES = [
    TestCase(
        test_id=f"test-{uuid.uuid4()}",
        story_id=SAMPLE_USER_STORIES[0].story_id,
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
        test_case_csv="Step,Description,Expected Result\n1,Navigate to login page,Login page displayed\n2,Click Forgot Password,Reset form displayed\n3,Enter valid email,Email field accepts input\n4,Click Submit,Success message shown and email sent"
    ),
    TestCase(
        test_id=f"test-{uuid.uuid4()}",
        story_id=SAMPLE_USER_STORIES[0].story_id,
        title="Password Reset - Invalid Email",
        description="Test the password reset functionality with an invalid email address",
        steps=[
            {"step": "1", "description": "Navigate to the login page"},
            {"step": "2", "description": "Click on 'Forgot Password' link"},
            {"step": "3", "description": "Enter an invalid email address (e.g., missing @ symbol)"},
            {"step": "4", "description": "Click 'Submit' button"}
        ],
        expected_result="System should display an error message about invalid email format",
        test_type="negative",
        test_case_text="# Password Reset - Invalid Email\n\nTest the password reset functionality with an invalid email address",
        test_case_csv="Step,Description,Expected Result\n1,Navigate to login page,Login page displayed\n2,Click Forgot Password,Reset form displayed\n3,Enter invalid email,No validation error yet\n4,Click Submit,Error message shown for invalid email"
    ),
    TestCase(
        test_id=f"test-{uuid.uuid4()}",
        story_id=SAMPLE_USER_STORIES[0].story_id,
        title="Password Reset - Non-existent User",
        description="Test the password reset functionality with an email that doesn't exist in the system",
        steps=[
            {"step": "1", "description": "Navigate to the login page"},
            {"step": "2", "description": "Click on 'Forgot Password' link"},
            {"step": "3", "description": "Enter an email address that doesn't exist in the system"},
            {"step": "4", "description": "Click 'Submit' button"}
        ],
        expected_result="System should display a generic success message (for security) but no email should be sent",
        test_type="edge",
        test_case_text="# Password Reset - Non-existent User\n\nTest the password reset functionality with an email that doesn't exist in the system",
        test_case_csv="Step,Description,Expected Result\n1,Navigate to login page,Login page displayed\n2,Click Forgot Password,Reset form displayed\n3,Enter non-existent email,Email field accepts input\n4,Click Submit,Generic success message shown but no email sent"
    )
]

def setup_argparse() -> argparse.ArgumentParser:
    """Set up argument parser for the script."""
    parser = argparse.ArgumentParser(description="Test the vector database independently")
    parser.add_argument(
        "--db-type", 
        choices=["weaviate", "qdrant"], 
        default=VECTOR_DB_TYPE,
        help="Type of vector database to test (default: from config)"
    )
    parser.add_argument(
        "--action",
        choices=["store", "retrieve", "health", "all"],
        default="all",
        help="Action to perform (default: all)"
    )
    parser.add_argument(
        "--query", 
        type=str,
        help="Query for search testing (default: use sample stories)"
    )
    return parser

def store_samples(vector_store):
    """Store sample user stories and test cases in the vector database."""
    print("Storing sample user stories and test cases...")
    
    # Store user stories
    story_ids = []
    for i, story in enumerate(SAMPLE_USER_STORIES):
        story_id = vector_store.store_user_story(story)
        story_ids.append(story_id)
        print(f"[{i+1}/{len(SAMPLE_USER_STORIES)}] Stored user story: {story.title} (ID: {story_id})")
    
    # Store test cases
    test_case_ids = []
    for i, test_case in enumerate(SAMPLE_TEST_CASES):
        test_id = vector_store.store_test_case(test_case)
        test_case_ids.append(test_id)
        print(f"[{i+1}/{len(SAMPLE_TEST_CASES)}] Stored test case: {test_case.title} (ID: {test_id})")
    
    print(f"\nSuccessfully stored {len(story_ids)} user stories and {len(test_case_ids)} test cases")
    return story_ids, test_case_ids

def retrieve_similar(vector_store, query_story=None):
    """Retrieve similar user stories and test cases from the vector database."""
    print("Retrieving similar user stories and test cases...")
    
    # Use a sample story or create one from the query for retrieval
    if query_story is None:
        # Use the last sample story as the query
        query_story = SAMPLE_USER_STORIES[-1]
        print(f"Query story: {query_story.title}")
    
    # Find similar user stories
    similar_stories = vector_store.find_similar_stories(query_story, limit=3)
    print(f"\nFound {len(similar_stories)} similar user stories:")
    for i, story in enumerate(similar_stories):
        print(f"[{i+1}] Title: {story['title']}")
        print(f"    Similarity: {story['similarity_score']:.4f}")
        print(f"    ID: {story['story_id']}")
        print(f"    Description: {story['description'][:100]}...")
    
    # Find similar test cases
    similar_tests = vector_store.find_similar_test_cases(query_story, limit=3)
    print(f"\nFound {len(similar_tests)} similar test cases:")
    for i, test in enumerate(similar_tests):
        print(f"[{i+1}] Title: {test['title']}")
        print(f"    Similarity: {test['similarity_score']:.4f}")
        print(f"    ID: {test['test_id']}")
        print(f"    Type: {test['test_type']}")
        print(f"    Description: {test['description'][:100]}...")
    
    return similar_stories, similar_tests

def check_health(vector_store):
    """Check the health of the vector database."""
    print("Checking vector database health...")
    
    is_healthy = vector_store.health_check()
    if is_healthy:
        print("✅ Vector database is healthy")
    else:
        print("❌ Vector database is NOT healthy")
    
    return is_healthy

def main():
    """Main function to run the vector database tests."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Override the vector DB type if specified
    if args.db_type:
        os.environ["VECTOR_DB_TYPE"] = args.db_type
    
    # Create an instance of the vector store
    try:
        vector_store = get_vector_store()
        print(f"Using vector database: {args.db_type}")
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        sys.exit(1)
    
    # Create a query story if query is specified
    query_story = None
    if args.query:
        query_story = UserStory(
            story_id=f"query-{uuid.uuid4()}",
            project_id="test-project",
            title="Query Story",
            description=args.query,
            created_at=datetime.now()
        )
    
    # Perform the requested action
    if args.action in ["store", "all"]:
        store_samples(vector_store)
        print()
    
    if args.action in ["retrieve", "all"]:
        retrieve_similar(vector_store, query_story)
        print()
    
    if args.action in ["health", "all"]:
        check_health(vector_store)
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
