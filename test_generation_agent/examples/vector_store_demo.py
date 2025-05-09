"""
Demo script for the vector store service.
Shows how to store and retrieve user stories and test cases from the vector database.
"""
import sys
import os
import asyncio
from pathlib import Path
import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the application components
from app.services.vector_store import (
    store_user_story,
    store_test_cases,
    search_similar_user_stories,
    search_similar_test_cases,
    ensure_schema_exists
)
from app.services.embedding import get_embedding
from app.models.data_models import UserStoryRecord, TestCaseRecord
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main function for the demo"""
    print("Vector Store Demo")
    print("================")
    
    # Check if vector database is configured
    if not os.environ.get("VECTOR_DB_URL"):
        print("Error: VECTOR_DB_URL environment variable not set.")
        print("Please set it in the .env file.")
        return
    
    # Ensure the schema exists in the vector database
    print("\nEnsuring schema exists in vector database...")
    if not await ensure_schema_exists():
        print("Error: Failed to ensure schema exists.")
        return
    
    print("Schema verified successfully.")
    
    # Create a sample user story
    print("\nCreating a sample user story...")
    user_story = UserStoryRecord(
        story_id="DEMO-001",
        project_id="DEMO-PROJECT",
        title="As a user, I want to reset my password",
        description="""
        As a user, I want to reset my password so that I can regain access to my account if I forget it.
        
        Acceptance Criteria:
        1. User can access the password reset page from the login screen
        2. User can submit their email address to receive a password reset link
        3. User receives a password reset email with a secure, time-limited link
        4. User can create a new password that meets the security requirements
        5. User is notified when the password has been successfully reset
        """,
        created_at=datetime.datetime.now()
    )
    
    # Generate embedding for the user story
    print("Generating embedding for the user story...")
    combined_text = f"{user_story.title}\n\n{user_story.description}"
    user_story.embedding = await get_embedding(combined_text)
    
    # Store the user story in the vector database
    print("Storing user story in vector database...")
    if not await store_user_story(user_story):
        print("Error: Failed to store user story.")
        return
    
    print("User story stored successfully.")
    
    # Create sample test cases
    print("\nCreating sample test cases...")
    test_cases = []
    
    # Test case 1: Successful password reset
    test_case1 = TestCaseRecord(
        story_id="DEMO-001",
        test_case_id="TC-001",
        title="Verify successful password reset flow",
        description="Test that a user can successfully reset their password",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed"},
            {"action": "Click on 'Forgot Password' link", "expected": "Password reset page is displayed"},
            {"action": "Enter registered email address", "expected": "Email is accepted"},
            {"action": "Click 'Send Reset Link' button", "expected": "Confirmation message is displayed"},
            {"action": "Open email and click on reset link", "expected": "New password page is displayed"},
            {"action": "Enter new password that meets requirements", "expected": "Password is accepted"},
            {"action": "Confirm new password", "expected": "Password is accepted"},
            {"action": "Click 'Reset Password' button", "expected": "Success message is displayed and user is redirected to login page"}
        ],
        test_case_text=(
            "# Verify successful password reset flow\n\n"
            "## Description\n"
            "Test that a user can successfully reset their password\n\n"
            "## Steps\n"
            "1. Navigate to login page\n"
            "   - Expected: Login page is displayed\n"
            "2. Click on 'Forgot Password' link\n"
            "   - Expected: Password reset page is displayed\n"
            "3. Enter registered email address\n"
            "   - Expected: Email is accepted\n"
            "4. Click 'Send Reset Link' button\n"
            "   - Expected: Confirmation message is displayed\n"
            "5. Open email and click on reset link\n"
            "   - Expected: New password page is displayed\n"
            "6. Enter new password that meets requirements\n"
            "   - Expected: Password is accepted\n"
            "7. Confirm new password\n"
            "   - Expected: Password is accepted\n"
            "8. Click 'Reset Password' button\n"
            "   - Expected: Success message is displayed and user is redirected to login page"
        ),
        generated_at=datetime.datetime.now()
    )
    test_cases.append(test_case1)
    
    # Test case 2: Invalid email
    test_case2 = TestCaseRecord(
        story_id="DEMO-001",
        test_case_id="TC-002",
        title="Verify error message with unregistered email",
        description="Test that appropriate error message is shown when unregistered email is provided",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed"},
            {"action": "Click on 'Forgot Password' link", "expected": "Password reset page is displayed"},
            {"action": "Enter unregistered email address", "expected": "Email is accepted"},
            {"action": "Click 'Send Reset Link' button", "expected": "Error message is displayed indicating email not found"}
        ],
        test_case_text=(
            "# Verify error message with unregistered email\n\n"
            "## Description\n"
            "Test that appropriate error message is shown when unregistered email is provided\n\n"
            "## Steps\n"
            "1. Navigate to login page\n"
            "   - Expected: Login page is displayed\n"
            "2. Click on 'Forgot Password' link\n"
            "   - Expected: Password reset page is displayed\n"
            "3. Enter unregistered email address\n"
            "   - Expected: Email is accepted\n"
            "4. Click 'Send Reset Link' button\n"
            "   - Expected: Error message is displayed indicating email not found"
        ),
        generated_at=datetime.datetime.now()
    )
    test_cases.append(test_case2)
    
    # Generate embeddings for the test cases
    print("Generating embeddings for test cases...")
    for test_case in test_cases:
        combined_text = f"{test_case.title}\n\n{test_case.description}\n\n{test_case.test_case_text}"
        test_case.embedding = await get_embedding(combined_text)
    
    # Store the test cases in the vector database
    print("Storing test cases in vector database...")
    if not await store_test_cases(test_cases):
        print("Error: Failed to store test cases.")
        return
    
    print("Test cases stored successfully.")
    
    # Search for similar user stories
    print("\nSearching for similar user stories...")
    query_text = "As a user, I want to change my password to improve security"
    query_embedding = await get_embedding(query_text)
    
    similar_stories = await search_similar_user_stories(query_embedding, limit=2)
    
    print(f"Found {len(similar_stories)} similar user stories:")
    for i, story in enumerate(similar_stories):
        print(f"\nSimilar User Story {i+1}:")
        print(f"ID: {story.story_id}")
        print(f"Title: {story.title}")
        print(f"Description: {story.description[:100]}...")
    
    # Search for similar test cases
    print("\nSearching for similar test cases...")
    query_text = "Test password reset with invalid email"
    query_embedding = await get_embedding(query_text)
    
    similar_test_cases = await search_similar_test_cases(query_embedding, limit=2)
    
    print(f"Found {len(similar_test_cases)} similar test cases:")
    for i, test_case in enumerate(similar_test_cases):
        print(f"\nSimilar Test Case {i+1}:")
        print(f"ID: {test_case.test_case_id}")
        print(f"Title: {test_case.title}")
        print(f"Description: {test_case.description}")
    
    print("\nDemo complete!")

if __name__ == "__main__":
    asyncio.run(main())
