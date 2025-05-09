"""
Data models used throughout the application.
Includes Pydantic models for request/response validation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class UserStoryWebhook(BaseModel):
    """Represents a user story from Azure DevOps webhook"""
    story_id: str
    project_id: str
    title: str
    description: str = ""
    event_type: str
    created_by: str = ""
    work_item_type: str

class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints"""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

class UserStoryRecord(BaseModel):
    """Represents a user story stored in the vector database"""
    story_id: str
    project_id: str
    title: str
    description: str = ""
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)

class TestCaseRecord(BaseModel):
    """Represents a test case stored in the vector database"""
    story_id: str
    test_case_id: Optional[str] = None  # ID in Azure DevOps
    title: str
    description: str
    steps: List[Dict[str, str]]  # List of steps with action and expected result
    test_case_text: str  # Markdown representation
    test_case_csv: Optional[str] = None  # CSV representation
    embedding: Optional[List[float]] = None
    generated_at: datetime = Field(default_factory=datetime.now)

class AgentInput(BaseModel):
    """Input to the LangGraph agent"""
    user_story: UserStoryRecord
    similar_stories: List[UserStoryRecord] = Field(default_factory=list)
    similar_test_cases: List[TestCaseRecord] = Field(default_factory=list)

class AgentOutput(BaseModel):
    """Output from the LangGraph agent"""
    user_story_id: str
    test_cases: List[TestCaseRecord]
    summary: str

class VectorSearchResult(BaseModel):
    """Result from a vector search operation"""
    object_id: str
    score: float
    data: Dict[str, Any]
