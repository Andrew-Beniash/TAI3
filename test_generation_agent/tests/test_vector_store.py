"""
Test script for the vector store service.
"""
import sys
import os
from pathlib import Path
import pytest
import asyncio
import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the vector store components
from app.services.vector_store import (
    ensure_schema_exists,
    store_user_story,
    store_test_cases,
    search_similar_user_stories,
    search_similar_test_cases
)
from app.models.data_models import UserStoryRecord, TestCaseRecord

@pytest.fixture
def sample_user_story():
    """Create a sample user story for testing"""
    return UserStoryRecord(
        story_id="TEST-VS-001",
        project_id="TEST-PROJECT",
        title="As a user, I want to search for products",
        description="""
        As a customer, I want to search for products by keyword so that I can find what I'm looking for quickly.
        
        Acceptance Criteria:
        1. User can enter search terms in the search box
        2. User can click the search button or press Enter to submit
        3. Search results display matching products with images and prices
        4. User can see how many results were found
        5. User receives a message when no results are found
        """,
        created_at=datetime.datetime.now(),
        embedding=[0.1] * 1536  # Mock embedding
    )

@pytest.fixture
def sample_test_cases():
    """Create sample test cases for testing"""
    test_case1 = TestCaseRecord(
        story_id="TEST-VS-001",
        test_case_id="TC-VS-001",
        title="Verify search with valid keyword returns results",
        description="Test that searching with a valid keyword returns matching products",
        steps=[
            {"action": "Navigate to the homepage", "expected": "Homepage is displayed with search box"},
            {"action": "Enter a valid keyword in the search box", "expected": "Keyword is entered"},
            {"action": "Click the search button", "expected": "Search results page is displayed"},
            {"action": "Verify search results", "expected": "Search results show matching products with images and prices"}
        ],
        test_case_text="Sample test case text",
        generated_at=datetime.datetime.now(),
        embedding=[0.2] * 1536  # Mock embedding
    )
    
    test_case2 = TestCaseRecord(
        story_id="TEST-VS-001",
        test_case_id="TC-VS-002",
        title="Verify search with no results shows appropriate message",
        description="Test that searching with a keyword that has no matches shows a 'no results' message",
        steps=[
            {"action": "Navigate to the homepage", "expected": "Homepage is displayed with search box"},
            {"action": "Enter a keyword with no matches", "expected": "Keyword is entered"},
            {"action": "Click the search button", "expected": "Search results page is displayed"},
            {"action": "Verify no results message", "expected": "Message indicating no results were found is displayed"}
        ],
        test_case_text="Sample test case text",
        generated_at=datetime.datetime.now(),
        embedding=[0.3] * 1536  # Mock embedding
    )
    
    return [test_case1, test_case2]

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_ensure_schema_exists():
    """Test ensuring the schema exists in the vector database"""
    # Call the function
    result = await ensure_schema_exists()
    
    # Check the result
    assert result is True

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_store_user_story(sample_user_story):
    """Test storing a user story in the vector database"""
    # Ensure the schema exists
    await ensure_schema_exists()
    
    # Store the user story
    result = await store_user_story(sample_user_story)
    
    # Check the result
    assert result is True

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_store_test_cases(sample_test_cases):
    """Test storing test cases in the vector database"""
    # Ensure the schema exists
    await ensure_schema_exists()
    
    # Store the test cases
    result = await store_test_cases(sample_test_cases)
    
    # Check the result
    assert result is True

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_search_similar_user_stories():
    """Test searching for similar user stories"""
    # Ensure the schema exists
    await ensure_schema_exists()
    
    # Create a query embedding
    query_embedding = [0.1] * 1536
    
    # Search for similar user stories
    results = await search_similar_user_stories(query_embedding, limit=2)
    
    # Check the results
    assert isinstance(results, list)

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_search_similar_test_cases():
    """Test searching for similar test cases"""
    # Ensure the schema exists
    await ensure_schema_exists()
    
    # Create a query embedding
    query_embedding = [0.2] * 1536
    
    # Search for similar test cases
    results = await search_similar_test_cases(query_embedding, limit=2)
    
    # Check the results
    assert isinstance(results, list)

@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("VECTOR_DB_URL"), reason="Vector DB URL not set")
async def test_full_vector_store_workflow(sample_user_story, sample_test_cases):
    """Test the full vector store workflow"""
    # Ensure the schema exists
    await ensure_schema_exists()
    
    # Store the user story
    store_story_result = await store_user_story(sample_user_story)
    assert store_story_result is True
    
    # Store the test cases
    store_cases_result = await store_test_cases(sample_test_cases)
    assert store_cases_result is True
    
    # Search for similar user stories
    similar_stories = await search_similar_user_stories(sample_user_story.embedding, limit=1)
    assert isinstance(similar_stories, list)
    
    # Search for similar test cases
    similar_test_cases = await search_similar_test_cases(sample_test_cases[0].embedding, limit=1)
    assert isinstance(similar_test_cases, list)

@pytest.mark.asyncio
async def test_vector_store_with_missing_url():
    """Test vector store functions when URL is not configured"""
    # Temporarily unset the VECTOR_DB_URL
    original_url = os.environ.get("VECTOR_DB_URL")
    if "VECTOR_DB_URL" in os.environ:
        del os.environ["VECTOR_DB_URL"]
    
    try:
        # Create mock data
        user_story = UserStoryRecord(
            story_id="TEST-MOCK-001",
            project_id="TEST-PROJECT",
            title="Mock User Story",
            description="Mock description",
            created_at=datetime.datetime.now(),
            embedding=[0.1] * 1536
        )
        
        test_case = TestCaseRecord(
            story_id="TEST-MOCK-001",
            test_case_id="TC-MOCK-001",
            title="Mock Test Case",
            description="Mock description",
            steps=[{"action": "Mock action", "expected": "Mock expected"}],
            test_case_text="Mock text",
            generated_at=datetime.datetime.now(),
            embedding=[0.2] * 1536
        )
        
        # Test the functions
        schema_result = await ensure_schema_exists()
        assert schema_result is False
        
        story_result = await store_user_story(user_story)
        assert story_result is False
        
        cases_result = await store_test_cases([test_case])
        assert cases_result is False
        
        similar_stories = await search_similar_user_stories([0.1] * 1536)
        assert similar_stories == []
        
        similar_cases = await search_similar_test_cases([0.2] * 1536)
        assert similar_cases == []
    
    finally:
        # Restore the original VECTOR_DB_URL
        if original_url:
            os.environ["VECTOR_DB_URL"] = original_url

if __name__ == "__main__":
    # Run the tests manually
    pytest.main(["-xvs", __file__])
