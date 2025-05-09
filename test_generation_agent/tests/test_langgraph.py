"""
Test script for the LangGraph agent.
"""
import sys
import os
from pathlib import Path
import pytest
import asyncio
import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the LangGraph components
from langgraph.qa_agent_graph import (
    create_agent_graph,
    analyze_user_story,
    generate_test_cases,
    process_user_story_with_langgraph
)
from app.models.data_models import UserStoryRecord, TestCaseRecord, AgentState

@pytest.fixture
def sample_user_story():
    """Create a sample user story for testing"""
    return UserStoryRecord(
        story_id="TEST-001",
        project_id="TEST-PROJECT",
        title="As a user, I want to log in to the application",
        description="""
        As a registered user, I want to log in to the application so that I can access my account.
        
        Acceptance Criteria:
        1. User can enter email and password
        2. User can click login button
        3. User is redirected to dashboard after successful login
        4. User sees error message for invalid credentials
        """,
        created_at=datetime.datetime.now()
    )

@pytest.fixture
def sample_similar_story():
    """Create a sample similar user story for testing"""
    return UserStoryRecord(
        story_id="TEST-002",
        project_id="TEST-PROJECT",
        title="As a user, I want to register a new account",
        description="""
        As a new user, I want to register a new account so that I can access the application.
        
        Acceptance Criteria:
        1. User can enter name, email, and password
        2. User can click register button
        3. User is redirected to login page after successful registration
        4. User sees error message for invalid inputs
        """,
        created_at=datetime.datetime.now()
    )

@pytest.fixture
def sample_similar_test_case():
    """Create a sample similar test case for testing"""
    return TestCaseRecord(
        story_id="TEST-002",
        test_case_id="TC-001",
        title="Verify successful registration",
        description="Test that a user can successfully register a new account",
        steps=[
            {"action": "Navigate to registration page", "expected": "Registration page is displayed"},
            {"action": "Enter valid name", "expected": "Name is accepted"},
            {"action": "Enter valid email", "expected": "Email is accepted"},
            {"action": "Enter valid password", "expected": "Password is accepted"},
            {"action": "Click register button", "expected": "Success message is displayed"}
        ],
        test_case_text="Sample test case text",
        generated_at=datetime.datetime.now()
    )

@pytest.fixture
def sample_agent_state(sample_user_story, sample_similar_story, sample_similar_test_case):
    """Create a sample agent state for testing"""
    return AgentState(
        messages=[],
        user_story=sample_user_story,
        similar_stories=[sample_similar_story],
        similar_test_cases=[sample_similar_test_case],
        analysis=None,
        test_cases=[]
    )

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_analyze_user_story(sample_agent_state):
    """Test the analyze_user_story function"""
    # Run the analyze_user_story function
    updated_state = analyze_user_story(sample_agent_state)
    
    # Check if the analysis is created
    assert updated_state["analysis"] is not None
    assert "key_features" in updated_state["analysis"]
    assert "user_roles" in updated_state["analysis"]
    assert "acceptance_criteria" in updated_state["analysis"]
    assert "edge_cases" in updated_state["analysis"]
    
    # Check if messages are updated
    assert len(updated_state["messages"]) > len(sample_agent_state["messages"])

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_generate_test_cases(sample_agent_state):
    """Test the generate_test_cases function"""
    # First run analyze_user_story to get the analysis
    state_with_analysis = analyze_user_story(sample_agent_state)
    
    # Run the generate_test_cases function
    updated_state = generate_test_cases(state_with_analysis)
    
    # Check if test cases are created
    assert len(updated_state["test_cases"]) > 0
    
    # Check the first test case
    test_case = updated_state["test_cases"][0]
    assert test_case.title
    assert test_case.description
    assert len(test_case.steps) > 0
    assert "action" in test_case.steps[0]
    assert "expected" in test_case.steps[0]

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_process_user_story_with_langgraph(sample_user_story, sample_similar_story, sample_similar_test_case):
    """Test the process_user_story_with_langgraph function"""
    # Run the process_user_story_with_langgraph function
    test_cases, summary = await process_user_story_with_langgraph(
        user_story=sample_user_story,
        similar_stories=[sample_similar_story],
        similar_test_cases=[sample_similar_test_case]
    )
    
    # Check if test cases are created
    assert len(test_cases) > 0
    assert summary
    
    # Check the first test case
    test_case = test_cases[0]
    assert test_case.title
    assert test_case.description
    assert len(test_case.steps) > 0

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OpenAI API key not set")
async def test_create_agent_graph():
    """Test creating the agent graph"""
    # Create the agent graph
    graph = create_agent_graph()
    
    # Check if the graph is created
    assert graph is not None

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-xvs", __file__])
