"""
Demo script for the Azure DevOps integration.
Shows how to create test cases in Azure DevOps using the service.
"""
import sys
import os
import asyncio
from pathlib import Path
import datetime

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import application components
from app.services.azure_devops import (
    get_user_story,
    create_test_cases_in_azure_devops,
    add_comment_to_user_story,
    mock_create_test_cases
)
from app.models.data_models import TestCaseRecord
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main function for the demo"""
    print("Azure DevOps Integration Demo")
    print("=============================")
    
    # Check if Azure DevOps credentials are set
    if not os.environ.get("AZURE_DEVOPS_PAT") or not os.environ.get("AZURE_DEVOPS_ORG"):
        print("Warning: Azure DevOps credentials not set.")
        print("Will use mock functions instead of actual Azure DevOps API.")
        use_mock = True
    else:
        use_mock = False
    
    # Define a sample user story ID
    story_id = "12345"  # Replace with an actual ID from your Azure DevOps project
    
    if not use_mock:
        # Get the user story from Azure DevOps
        print(f"\nFetching user story {story_id} from Azure DevOps...")
        story_data = await get_user_story(story_id)
        
        if not story_data:
            print(f"Error: User story {story_id} not found in Azure DevOps.")
            print("Will continue with mock data.")
            use_mock = True
        else:
            print(f"User story fetched successfully:")
            print(f"Title: {story_data.get('title', '')}")
            print(f"Type: {story_data.get('work_item_type', '')}")
            print(f"State: {story_data.get('state', '')}")
    
    # Create sample test cases
    print("\nCreating sample test cases...")
    test_cases = []
    
    # Test case 1
    test_case1 = TestCaseRecord(
        story_id=story_id,
        title="Verify user can view profile settings",
        description="Test that a user can navigate to and view their profile settings",
        steps=[
            {"action": "Log in to the application", "expected": "User is logged in and dashboard is displayed"},
            {"action": "Click on user icon in top-right corner", "expected": "User dropdown menu is displayed"},
            {"action": "Click on 'Profile Settings'", "expected": "Profile settings page is displayed with user information"}
        ],
        test_case_text="Verify user can view profile settings",
        generated_at=datetime.datetime.now()
    )
    test_cases.append(test_case1)
    
    # Test case 2
    test_case2 = TestCaseRecord(
        story_id=story_id,
        title="Verify user can update profile information",
        description="Test that a user can update their profile information and changes are saved",
        steps=[
            {"action": "Navigate to profile settings", "expected": "Profile settings page is displayed"},
            {"action": "Edit name field", "expected": "Name field accepts input"},
            {"action": "Edit email field", "expected": "Email field accepts input"},
            {"action": "Click 'Save Changes' button", "expected": "Success message is displayed and changes are reflected in the profile"}
        ],
        test_case_text="Verify user can update profile information",
        generated_at=datetime.datetime.now()
    )
    test_cases.append(test_case2)
    
    # Create test cases in Azure DevOps
    print(f"\nCreating {len(test_cases)} test cases in Azure DevOps...")
    
    if use_mock:
        # Use mock function
        result = await mock_create_test_cases(story_id, test_cases)
        print("Using mock function (no actual API calls)")
    else:
        # Use actual API
        result = await create_test_cases_in_azure_devops(story_id, test_cases)
    
    if "error" in result:
        print(f"Error creating test cases: {result['error']}")
    else:
        print(f"Created {result['created_test_cases']} test cases successfully!")
        print(f"Test case IDs: {result['test_case_ids']}")
    
    # Add a comment to the user story
    if not use_mock:
        print("\nAdding comment to user story...")
        comment_text = f"Generated {len(test_cases)} test cases automatically using Test Generation Agent."
        
        success = await add_comment_to_user_story(story_id, comment_text)
        if success:
            print("Comment added successfully!")
        else:
            print("Error adding comment.")
    
    print("\nDemo complete!")

if __name__ == "__main__":
    asyncio.run(main())
