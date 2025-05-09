"""
Tests for the LangGraph agent implementation.
"""
import pytest
import asyncio
from typing import Dict, Any, List

from app.models.data_models import UserStory
from langgraph.qa_agent_graph import TestCaseGenerator

@pytest.fixture
def user_story() -> UserStory:
    """Fixture for a sample user story."""
    return UserStory(
        story_id="US123",
        project_id="Project1",
        title="User can reset password",
        description="""
        As a user, I want to be able to reset my password if I forget it, so that I can regain access to my account.
        
        Acceptance Criteria:
        - User can request a password reset from the login page
        - System sends a password reset link to the user's email
        - User can create a new password via the reset link
        - Link expires after 24 hours
        - New password must meet the system's password requirements
        """
    )

@pytest.mark.asyncio
async def test_generate_test_cases(user_story: UserStory):
    """Test generating test cases for a user story."""
    # Create a test case generator
    generator = TestCaseGenerator()
    
    # Generate test cases
    test_cases, message = await generator.generate_test_cases(user_story)
    
    # Check the results
    assert len(test_cases) > 0, "Should generate at least one test case"
    assert "successfully" in message, f"Message should indicate success, got: {message}"
    
    # Check the test case structure
    for tc in test_cases:
        assert tc.story_id == user_story.story_id, "Test case should reference the original story"
        assert tc.title, "Test case should have a title"
        assert tc.description, "Test case should have a description"
        assert len(tc.steps) > 0, "Test case should have steps"
        assert tc.expected_result, "Test case should have an expected result"
        assert tc.test_type in ["positive", "negative", "edge"], f"Test type should be valid, got: {tc.test_type}"
        assert tc.test_case_text, "Test case should have markdown text"
        assert tc.test_case_csv, "Test case should have CSV representation"

@pytest.mark.asyncio
async def test_generate_test_cases_with_context(user_story: UserStory):
    """Test generating test cases with similar stories and test cases as context."""
    # Create a test case generator
    generator = TestCaseGenerator()
    
    # Create a similar story
    similar_story = {
        "story_id": "US100",
        "title": "User can change password",
        "description": "As a user, I want to change my password from my profile page.",
        "similarity_score": 0.85
    }
    
    # Create a similar test case
    similar_test_case = {
        "test_id": "TC100",
        "story_id": "US100",
        "title": "Change Password - Valid New Password",
        "test_type": "positive",
        "test_case_text": """
        # Change Password - Valid New Password
        Test that a user can change their password with a valid new password
        
        ## Steps
        1. Log in with valid credentials
        2. Navigate to profile page
        3. Click on "Change Password" button
        4. Enter current password correctly
        5. Enter new password that meets requirements
        6. Confirm new password
        7. Click "Save" button
        
        ## Expected Result
        Password is changed successfully and user receives confirmation message
        """,
        "similarity_score": 0.8
    }
    
    # Generate test cases with context
    test_cases, message = await generator.generate_test_cases(
        user_story=user_story,
        similar_stories=[similar_story],
        similar_test_cases=[similar_test_case]
    )
    
    # Check the results
    assert len(test_cases) > 0, "Should generate at least one test case"
    assert "successfully" in message, f"Message should indicate success, got: {message}"
    
    # Check if we have different types of test cases
    test_types = set(tc.test_type for tc in test_cases)
    assert len(test_types) > 1, "Should generate different types of test cases"
