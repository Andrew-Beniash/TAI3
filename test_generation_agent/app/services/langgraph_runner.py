"""
LangGraph agent invocation logic.
Handles the execution of the LangGraph QA agent for test case generation.
"""
import logging
from typing import Dict, Any, List, Optional
import asyncio

from app.models.data_models import UserStoryWebhook, AgentInput, AgentOutput, UserStoryRecord, TestCaseRecord
from app.services.embedding import get_embedding
from app.services.vector_store import (
    store_user_story, 
    store_test_cases, 
    search_similar_user_stories, 
    search_similar_test_cases
)
from app.services.azure_devops import create_test_cases_in_azure_devops

# Configure logging
logger = logging.getLogger(__name__)

async def process_user_story(user_story: UserStoryWebhook) -> Dict[str, Any]:
    """
    Process a user story from a webhook and generate test cases.
    
    This is the main coordination function that:
    1. Converts webhook data to a UserStoryRecord
    2. Gets embedding for the user story
    3. Searches for similar stories and test cases
    4. Invokes the LangGraph agent
    5. Stores the results in the vector database
    6. Creates test cases in Azure DevOps
    
    Args:
        user_story: The user story webhook data
        
    Returns:
        Dict[str, Any]: Result of the processing with statistics
    """
    try:
        logger.info(f"Processing user story {user_story.story_id}: {user_story.title}")
        
        # Convert webhook data to UserStoryRecord
        story_record = UserStoryRecord(
            story_id=user_story.story_id,
            project_id=user_story.project_id,
            title=user_story.title,
            description=user_story.description
        )
        
        # Get embedding for the user story
        # TODO: Uncomment when embedding service is implemented
        # story_record.embedding = await get_embedding(
        #     f"{story_record.title}\n\n{story_record.description}"
        # )
        
        # For now, mock the embedding as a list of 1536 zeros
        story_record.embedding = [0.0] * 1536
        
        # Store the user story in the vector database
        # TODO: Uncomment when vector store is implemented
        # await store_user_story(story_record)
        
        # Search for similar user stories and test cases
        # TODO: Uncomment when vector store is implemented
        # similar_stories = await search_similar_user_stories(story_record.embedding, limit=3)
        # similar_test_cases = await search_similar_test_cases(story_record.embedding, limit=5)
        
        # For now, mock the similar stories and test cases
        similar_stories = []
        similar_test_cases = []
        
        # Prepare input for the LangGraph agent
        agent_input = AgentInput(
            user_story=story_record,
            similar_stories=similar_stories,
            similar_test_cases=similar_test_cases
        )
        
        # Invoke the LangGraph agent (will be implemented later)
        # TODO: Replace with actual LangGraph agent invocation
        agent_output = await mock_agent_output(agent_input)
        
        # Store the test cases in the vector database
        # TODO: Uncomment when vector store is implemented
        # await store_test_cases(agent_output.test_cases)
        
        # Create test cases in Azure DevOps
        # TODO: Uncomment when Azure DevOps service is implemented
        # azure_devops_result = await create_test_cases_in_azure_devops(
        #     user_story.story_id, 
        #     agent_output.test_cases
        # )
        
        # For now, mock the Azure DevOps result
        azure_devops_result = {
            "created_test_cases": len(agent_output.test_cases),
            "test_case_ids": [f"TC-{i+1}" for i in range(len(agent_output.test_cases))]
        }
        
        # Prepare the result
        result = {
            "story_id": user_story.story_id,
            "test_case_count": len(agent_output.test_cases),
            "test_case_ids": azure_devops_result.get("test_case_ids", []),
            "summary": agent_output.summary
        }
        
        logger.info(f"Generated {result['test_case_count']} test cases for user story {user_story.story_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing user story: {str(e)}", exc_info=True)
        raise

async def mock_agent_output(agent_input: AgentInput) -> AgentOutput:
    """
    Mock function that simulates the output of the LangGraph agent.
    Will be replaced with actual agent invocation.
    
    Args:
        agent_input: Input to the agent
        
    Returns:
        AgentOutput: Simulated agent output
    """
    # Simulate agent processing time
    await asyncio.sleep(1)
    
    # Create mock test cases
    test_cases = []
    
    # Login test case
    login_test = TestCaseRecord(
        story_id=agent_input.user_story.story_id,
        title="Verify successful login with valid credentials",
        description="Test that a user can successfully log in with valid credentials",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed with email and password fields"},
            {"action": "Enter valid email address", "expected": "Email is accepted without errors"},
            {"action": "Enter valid password", "expected": "Password is masked and accepted"},
            {"action": "Click Login button", "expected": "User is successfully authenticated and redirected to dashboard"}
        ],
        test_case_text=(
            "# Verify successful login with valid credentials\n\n"
            "## Description\n"
            "Test that a user can successfully log in with valid credentials\n\n"
            "## Steps\n"
            "1. Navigate to login page\n"
            "   - Expected: Login page is displayed with email and password fields\n"
            "2. Enter valid email address\n"
            "   - Expected: Email is accepted without errors\n"
            "3. Enter valid password\n"
            "   - Expected: Password is masked and accepted\n"
            "4. Click Login button\n"
            "   - Expected: User is successfully authenticated and redirected to dashboard"
        ),
        test_case_csv="Action,Expected Result\nNavigate to login page,Login page is displayed with email and password fields\nEnter valid email address,Email is accepted without errors\nEnter valid password,Password is masked and accepted\nClick Login button,User is successfully authenticated and redirected to dashboard"
    )
    test_cases.append(login_test)
    
    # Invalid login test case
    invalid_login_test = TestCaseRecord(
        story_id=agent_input.user_story.story_id,
        title="Verify error message with invalid credentials",
        description="Test that appropriate error message is shown when invalid credentials are provided",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed with email and password fields"},
            {"action": "Enter valid email address", "expected": "Email is accepted without errors"},
            {"action": "Enter invalid password", "expected": "Password is masked and accepted"},
            {"action": "Click Login button", "expected": "Error message is displayed indicating invalid credentials"}
        ],
        test_case_text=(
            "# Verify error message with invalid credentials\n\n"
            "## Description\n"
            "Test that appropriate error message is shown when invalid credentials are provided\n\n"
            "## Steps\n"
            "1. Navigate to login page\n"
            "   - Expected: Login page is displayed with email and password fields\n"
            "2. Enter valid email address\n"
            "   - Expected: Email is accepted without errors\n"
            "3. Enter invalid password\n"
            "   - Expected: Password is masked and accepted\n"
            "4. Click Login button\n"
            "   - Expected: Error message is displayed indicating invalid credentials"
        ),
        test_case_csv="Action,Expected Result\nNavigate to login page,Login page is displayed with email and password fields\nEnter valid email address,Email is accepted without errors\nEnter invalid password,Password is masked and accepted\nClick Login button,Error message is displayed indicating invalid credentials"
    )
    test_cases.append(invalid_login_test)
    
    # Forgot password test case
    forgot_password_test = TestCaseRecord(
        story_id=agent_input.user_story.story_id,
        title="Verify forgot password functionality",
        description="Test that a user can request a password reset using the forgot password feature",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed with email and password fields"},
            {"action": "Click on 'Forgot Password' link", "expected": "Forgot password page is displayed"},
            {"action": "Enter registered email address", "expected": "Email field accepts the input"},
            {"action": "Click on 'Reset Password' button", "expected": "Confirmation message is displayed indicating password reset instructions have been sent"}
        ],
        test_case_text=(
            "# Verify forgot password functionality\n\n"
            "## Description\n"
            "Test that a user can request a password reset using the forgot password feature\n\n"
            "## Steps\n"
            "1. Navigate to login page\n"
            "   - Expected: Login page is displayed with email and password fields\n"
            "2. Click on 'Forgot Password' link\n"
            "   - Expected: Forgot password page is displayed\n"
            "3. Enter registered email address\n"
            "   - Expected: Email field accepts the input\n"
            "4. Click on 'Reset Password' button\n"
            "   - Expected: Confirmation message is displayed indicating password reset instructions have been sent"
        ),
        test_case_csv="Action,Expected Result\nNavigate to login page,Login page is displayed with email and password fields\nClick on 'Forgot Password' link,Forgot password page is displayed\nEnter registered email address,Email field accepts the input\nClick on 'Reset Password' button,Confirmation message is displayed indicating password reset instructions have been sent"
    )
    test_cases.append(forgot_password_test)
    
    return AgentOutput(
        user_story_id=agent_input.user_story.story_id,
        test_cases=test_cases,
        summary=f"Generated {len(test_cases)} test cases for user story: '{agent_input.user_story.title}'"
    )
