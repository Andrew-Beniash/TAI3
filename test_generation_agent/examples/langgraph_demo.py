"""
Demo script for the LangGraph agent.
Shows how to generate test cases for a user story.
"""
import sys
import os
import asyncio
from pathlib import Path
import datetime
import json

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import application components
from langgraph.qa_agent_graph import process_user_story_with_langgraph
from app.models.data_models import UserStoryRecord, TestCaseRecord
from app.utils.csv_writer import generate_csv_from_test_cases
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main function for the demo"""
    print("LangGraph Agent Demo")
    print("===================")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it in the .env file.")
        return
    
    # Create a sample user story
    print("\nCreating a sample user story...")
    user_story = UserStoryRecord(
        story_id="DEMO-002",
        project_id="DEMO-PROJECT",
        title="As a user, I want to update my profile information",
        description="""
        As a user, I want to update my profile information so that I can keep my account details current.
        
        Acceptance Criteria:
        1. User can navigate to their profile settings
        2. User can edit their name, email, and phone number
        3. User can upload or change their profile picture
        4. User receives confirmation when profile is updated successfully
        5. Changes are reflected immediately across the platform
        6. User is prevented from entering invalid data formats
        """,
        created_at=datetime.datetime.now()
    )
    
    # Create some sample similar stories for context
    print("Creating sample similar stories for context...")
    similar_story = UserStoryRecord(
        story_id="DEMO-SIMILAR-001",
        project_id="DEMO-PROJECT",
        title="As a user, I want to change my password",
        description="""
        As a user, I want to change my password so that I can maintain the security of my account.
        
        Acceptance Criteria:
        1. User can navigate to password settings from their profile
        2. User must enter their current password for verification
        3. User can enter a new password that meets security requirements
        4. User can confirm the new password
        5. User receives confirmation when password is changed successfully
        """,
        created_at=datetime.datetime.now()
    )
    
    # Create some sample similar test cases for context
    print("Creating sample similar test cases for context...")
    similar_test_case = TestCaseRecord(
        story_id="DEMO-SIMILAR-001",
        test_case_id="TC-SIMILAR-001",
        title="Verify successful password change",
        description="Test that a user can successfully change their password",
        steps=[
            {"action": "Navigate to profile settings", "expected": "Profile settings page is displayed"},
            {"action": "Click on 'Change Password'", "expected": "Change password form is displayed"},
            {"action": "Enter current password", "expected": "Current password is accepted"},
            {"action": "Enter new password", "expected": "New password is accepted"},
            {"action": "Confirm new password", "expected": "Password confirmation is accepted"},
            {"action": "Click 'Save Changes' button", "expected": "Success message is displayed"}
        ],
        test_case_text="Sample test case text",
        generated_at=datetime.datetime.now()
    )
    
    # Process the user story with the LangGraph agent
    print("\nProcessing user story with LangGraph agent...")
    print("This may take a moment...")
    
    test_cases, summary = await process_user_story_with_langgraph(
        user_story=user_story,
        similar_stories=[similar_story],
        similar_test_cases=[similar_test_case]
    )
    
    # Print the results
    print("\nAgent completed successfully!")
    print(f"Summary: {summary}")
    print(f"Generated {len(test_cases)} test cases:")
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_case.title}")
        print(f"Description: {test_case.description}")
        print("Steps:")
        for j, step in enumerate(test_case.steps):
            print(f"  {j+1}. {step['action']}")
            print(f"     Expected: {step['expected']}")
    
    # Generate CSV from test cases
    print("\nGenerating CSV from test cases...")
    csv_output = generate_csv_from_test_cases(test_cases)
    
    # Save CSV to file
    csv_file = Path("generated_test_cases.csv")
    with open(csv_file, "w") as f:
        f.write(csv_output)
    
    print(f"CSV file saved to {csv_file.absolute()}")
    
    print("\nDemo complete!")

if __name__ == "__main__":
    asyncio.run(main())
