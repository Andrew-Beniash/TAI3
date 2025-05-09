"""
TypedDict definitions for LangGraph agent state.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

from app.models.data_models import UserStoryRecord, TestCaseRecord

class AgentState(TypedDict):
    """Type for the agent state."""
    messages: List[BaseMessage]
    user_story: UserStoryRecord
    similar_stories: List[UserStoryRecord]
    similar_test_cases: List[TestCaseRecord]
    analysis: Optional[Dict[str, Any]]
    test_cases: List[TestCaseRecord]
