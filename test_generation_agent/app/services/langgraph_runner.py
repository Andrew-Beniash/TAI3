"""
LangGraph runner service for the QA Agent application.
Handles the execution of the LangGraph agent.
"""
import logging
from typing import List, Dict, Any, Tuple

from app.models.data_models import UserStory, TestCase
from app.services.vector_store import get_vector_store
from langgraph.qa_agent_graph import TestCaseGenerator

logger = logging.getLogger(__name__)

class LangGraphService:
    """Service for running the LangGraph agent."""
    
    def __init__(self):
        """Initialize the LangGraph service."""
        self.vector_store = get_vector_store()
        self.generator = TestCaseGenerator()
    
    async def generate_test_cases(self, user_story: UserStory) -> Tuple[List[TestCase], str]:
        """
        Generate test cases for a user story.
        
        Args:
            user_story: The user story to generate test cases for
            
        Returns:
            Tuple of (list of test cases, message)
        """
        try:
            logger.info(f"Generating test cases for user story {user_story.story_id}")
            
            # Check if the user story has an embedding, if not create one
            if not user_story.embedding:
                # Store the user story in the vector store and get similar stories and test cases
                self.vector_store.store_user_story(user_story)
            
            # Find similar user stories and test cases
            similar_stories = self.vector_store.find_similar_stories(user_story)
            similar_test_cases = self.vector_store.find_similar_test_cases(user_story)
            
            # Generate test cases
            test_cases, message = await self.generator.generate_test_cases(
                user_story=user_story,
                similar_stories=similar_stories,
                similar_test_cases=similar_test_cases
            )
            
            # Store the generated test cases in the vector store
            for test_case in test_cases:
                self.vector_store.store_test_case(test_case)
            
            return test_cases, message
            
        except Exception as e:
            logger.error(f"Error in LangGraph service: {e}")
            return [], f"Failed to generate test cases: {str(e)}"
