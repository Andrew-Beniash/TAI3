"""
TypedDict definitions for the LangGraph agent state.
These define the structure of data passed between nodes in the LangGraph.
"""
from typing import TypedDict, List, Dict, Any, Optional

class SimilarStory(TypedDict):
    """Represents a similar user story retrieved from the vector store."""
    story_id: str
    title: str
    description: str
    similarity_score: float

class SimilarTestCase(TypedDict):
    """Represents a similar test case retrieved from the vector store."""
    test_id: str
    story_id: str
    test_type: str
    test_case_text: str
    similarity_score: float

class GeneratedTestCase(TypedDict):
    """Represents a generated test case in the agent state."""
    title: str
    description: str
    steps: List[Dict[str, str]]
    expected_result: str
    test_type: str
    test_case_text: str
    test_case_csv: str

class AgentState(TypedDict):
    """The state object passed between nodes in the LangGraph agent."""
    user_story: Dict[str, Any]  # The current user story being processed
    similar_stories: List[SimilarStory]  # Similar user stories from vector DB
    similar_test_cases: List[SimilarTestCase]  # Similar test cases from vector DB
    generated_test_cases: List[GeneratedTestCase]  # Generated test cases
    error: Optional[str]  # Error message, if any
