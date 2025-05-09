"""
LangGraph QA Agent Implementation.
Defines the agent graph with nodes for retrieving context and generating test cases.
"""
import json
import logging
from typing import Dict, List, Any, Tuple, Annotated, TypedDict

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation

from app.config import OPENAI_API_KEY, LLM_MODEL, PERSISTENCE_PATH
from app.models.agent_state import AgentState, SimilarStory, SimilarTestCase
from app.models.data_models import UserStory, TestCase
from app.prompts.test_case_prompts import (
    context_prompt_template, 
    test_case_generation_template,
    retrieve_context_template,
    format_test_cases_template
)
from app.utils.csv_writer import test_case_to_csv, markdown_to_test_case

logger = logging.getLogger(__name__)

# Initialize the LLM
llm = ChatOpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY, temperature=0.7)

def retrieve_similar_cases(state: AgentState) -> AgentState:
    """
    First node in the graph. This node would normally retrieve similar cases
    from a vector store, but for now, it just passes through the state.
    In a real implementation, this would use a vector DB service.
    """
    logger.info("Retrieving similar cases")
    
    # For demonstration purposes, we're not actually retrieving from a vector store
    # In a real implementation, this would use the vector_store service
    
    # Create dummy similar stories if none provided (for testing)
    if "similar_stories" not in state or not state["similar_stories"]:
        state["similar_stories"] = []
    
    # Create dummy similar test cases if none provided (for testing)
    if "similar_test_cases" not in state or not state["similar_test_cases"]:
        state["similar_test_cases"] = []
    
    return state

def generate_test_cases(state: AgentState) -> AgentState:
    """Generate test cases based on the user story and similar cases."""
    logger.info("Generating test cases")
    
    user_story = state["user_story"]
    similar_stories = state.get("similar_stories", [])
    similar_test_cases = state.get("similar_test_cases", [])
    
    # Prepare context examples string
    context_examples = ""
    
    # Format similar stories
    if similar_stories:
        context_examples += "### SIMILAR USER STORIES:\n\n"
        for story in similar_stories:
            context_examples += f"**User Story**: {story['title']}\n"
            context_examples += f"**Description**: {story['description']}\n\n"
    
    # Format similar test cases
    if similar_test_cases:
        context_examples += "### SIMILAR TEST CASES:\n\n"
        for tc in similar_test_cases:
            context_examples += f"**Test Case**: {tc['title']}\n"
            context_examples += f"**Type**: {tc['test_type']}\n"
            context_examples += f"**Steps**: {tc['test_case_text']}\n\n"
    
    # Format user story details
    user_story_details = f"""
Title: {user_story['title']}
Description: {user_story['description']}
"""
    
    # Prepare the context for test case generation
    context = context_prompt_template.format(
        user_story_details=user_story_details,
        context_examples=context_examples or "No similar examples found."
    )
    
    # Generate test cases using the LLM
    prompt = test_case_generation_template.format(context=context)
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Parse the generated test cases
    try:
        test_cases_text = response.content
        
        # Split the markdown text into individual test cases
        test_case_sections = []
        current_section = ""
        for line in test_cases_text.split('\n'):
            if line.startswith('# ') and current_section:  # New test case starts
                test_case_sections.append(current_section.strip())
                current_section = line
            else:
                current_section += "\n" + line
        
        if current_section:  # Add the last section
            test_case_sections.append(current_section.strip())
        
        # Parse each test case section into a structured format
        generated_test_cases = []
        for tc_text in test_case_sections:
            parsed_tc = markdown_to_test_case(tc_text)
            if parsed_tc:
                # Generate CSV format
                parsed_tc["test_case_csv"] = test_case_to_csv(parsed_tc)
                generated_test_cases.append(parsed_tc)
        
        state["generated_test_cases"] = generated_test_cases
        
    except Exception as e:
        logger.error(f"Error parsing generated test cases: {e}")
        state["error"] = f"Failed to parse generated test cases: {str(e)}"
    
    return state

def format_output(state: AgentState) -> AgentState:
    """Format the test cases for output."""
    logger.info("Formatting output")
    
    user_story = state["user_story"]
    generated_test_cases = state.get("generated_test_cases", [])
    
    # If there are no generated test cases or there was an error, return the state as is
    if not generated_test_cases or "error" in state:
        return state
    
    # For each test case, ensure it has all required fields
    for tc in generated_test_cases:
        if "test_case_csv" not in tc:
            tc["test_case_csv"] = test_case_to_csv(tc)
    
    return state

def create_agent() -> StateGraph:
    """Create the LangGraph agent with all nodes."""
    # Define the agent state structure
    graph = StateGraph(AgentState)
    
    # Add nodes to the graph
    graph.add_node("retrieve_similar_cases", retrieve_similar_cases)
    graph.add_node("generate_test_cases", generate_test_cases)
    graph.add_node("format_output", format_output)
    
    # Define the edges between nodes
    graph.add_edge("retrieve_similar_cases", "generate_test_cases")
    graph.add_edge("generate_test_cases", "format_output")
    graph.add_edge("format_output", END)
    
    # Set the entry point
    graph.set_entry_point("retrieve_similar_cases")
    
    # Compile the graph
    return graph.compile()

class TestCaseGenerator:
    """Main class for generating test cases from user stories."""
    
    def __init__(self):
        """Initialize the test case generator with an agent and vector store."""
        self.agent = create_agent()
    
    async def generate_test_cases(
        self, 
        user_story: UserStory,
        similar_stories: List[SimilarStory] = None,
        similar_test_cases: List[SimilarTestCase] = None
    ) -> Tuple[List[TestCase], str]:
        """
        Generate test cases for a user story.
        
        Args:
            user_story: The user story to generate test cases for
            similar_stories: Optional list of similar user stories
            similar_test_cases: Optional list of similar test cases
            
        Returns:
            Tuple of (list of test cases, message)
        """
        # Prepare the initial state
        initial_state: AgentState = {
            "user_story": {
                "story_id": user_story.story_id,
                "title": user_story.title,
                "description": user_story.description
            },
            "similar_stories": similar_stories or [],
            "similar_test_cases": similar_test_cases or [],
            "generated_test_cases": [],
            "error": None
        }
        
        # Run the agent
        try:
            final_state = await self.agent.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("error"):
                return [], final_state["error"]
            
            # Convert generated test cases to TestCase objects
            test_cases = []
            for tc in final_state.get("generated_test_cases", []):
                test_case = TestCase(
                    story_id=user_story.story_id,
                    title=tc["title"],
                    description=tc["description"],
                    steps=tc["steps"],
                    expected_result=tc["expected_result"],
                    test_type=tc["test_type"],
                    test_case_text=tc["test_case_text"],
                    test_case_csv=tc["test_case_csv"]
                )
                test_cases.append(test_case)
            
            return test_cases, "Test cases generated successfully"
            
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return [], f"Failed to generate test cases: {str(e)}"
