"""
Example script demonstrating how to use the Azure DevOps service.
This script shows how to:
1. Connect to Azure DevOps using a Personal Access Token
2. Create test cases using the Test Plans API
3. Link test cases to a user story using WorkItemRelation

Usage:
    python azure_devops_example.py

Requirements:
    - Valid Azure DevOps organization, project, and PAT in .env file
    - Existing user story in Azure DevOps
"""
import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.azure_devops import AzureDevOpsService
from app.models.data_models import TestCaseRecord

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to demonstrate Azure DevOps integration."""
    # Replace with your user story ID from Azure DevOps
    user_story_id = 123  # Replace with an actual user story ID
    
    try:
        # Initialize the Azure DevOps service
        azure_devops = AzureDevOpsService()
        
        # Create test case records
        test_cases = [
            TestCaseRecord(
                story_id=str(user_story_id),
                title="Positive Test Case - Valid Login",
                description="Test valid user login functionality",
                steps=[
                    {"action": "Navigate to login page", "expected": "Login page is displayed"},
                    {"action": "Enter valid username and password", "expected": "Credentials are accepted"},
                    {"action": "Click login button", "expected": "User is logged in and redirected to dashboard"}
                ],
                test_case_text="# Positive Test Case - Valid Login\n\n## Description\nTest valid user login functionality\n\n## Steps\n1. Navigate to login page\n   - Expected: Login page is displayed\n2. Enter valid username and password\n   - Expected: Credentials are accepted\n3. Click login button\n   - Expected: User is logged in and redirected to dashboard"
            ),
            TestCaseRecord(
                story_id=str(user_story_id),
                title="Negative Test Case - Invalid Credentials",
                description="Test login with invalid credentials",
                steps=[
                    {"action": "Navigate to login page", "expected": "Login page is displayed"},
                    {"action": "Enter invalid username and password", "expected": "Credentials are rejected"},
                    {"action": "Click login button", "expected": "Error message is displayed and user remains on login page"}
                ],
                test_case_text="# Negative Test Case - Invalid Credentials\n\n## Description\nTest login with invalid credentials\n\n## Steps\n1. Navigate to login page\n   - Expected: Login page is displayed\n2. Enter invalid username and password\n   - Expected: Credentials are rejected\n3. Click login button\n   - Expected: Error message is displayed and user remains on login page"
            )
        ]
        
        # Create test cases in Azure DevOps and link them to the user story
        created_test_cases = azure_devops.create_test_cases_for_story(
            user_story_id,
            test_cases,
            plan_name=f"Test Plan for Story {user_story_id}",
            suite_name=f"Test Suite for Story {user_story_id}"
        )
        
        logger.info(f"Successfully created {len(created_test_cases)} test cases for user story {user_story_id}")
        
        # Print details of created test cases
        for i, tc in enumerate(created_test_cases, start=1):
            logger.info(f"Test Case {i}:")
            logger.info(f"  ID: {tc.get('id')}")
            logger.info(f"  URL: {tc.get('_links', {}).get('html', {}).get('href')}")
        
    except Exception as e:
        logger.error(f"Error in Azure DevOps integration: {e}")
        raise

if __name__ == "__main__":
    main()
