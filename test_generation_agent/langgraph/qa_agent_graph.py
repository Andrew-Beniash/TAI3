"""
LangGraph agent for generating test cases.
This module contains the graph definition for the QA agent.
"""
import logging
import json
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Tuple

# Import langgraph components
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint import MemorySaver

# Import langgraph memory saver
from langgraph.checkpoint.sqlite import SqliteSaver

# Import LangChain components
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# Import application components
from app.config import OPENAI_API_KEY, OPENAI_COMPLETION_MODEL
from app.models.data_models import UserStoryRecord, TestCaseRecord
from app.prompts.test_case_prompts import (
    SYSTEM_PROMPT,
    USER_STORY_TEMPLATE,
    ANALYZE_USER_STORY_TEMPLATE,
    GENERATE_TEST_CASES_TEMPLATE
)

# Configure logging
logger = logging.getLogger(__name__)

# Define the agent state type
class AgentState(TypedDict):
    """Type for the agent state."""
    messages: List[BaseMessage]
    user_story: UserStoryRecord
    similar_stories: List[UserStoryRecord]
    similar_test_cases: List[TestCaseRecord]
    analysis: Optional[Dict[str, Any]]
    test_cases: List[TestCaseRecord]

# Initialize the LLM
model = ChatOpenAI(
    model=OPENAI_COMPLETION_MODEL,
    temperature=0.2,
    api_key=OPENAI_API_KEY
)

# Define the nodes for the graph
def analyze_user_story(state: AgentState) -> AgentState:
    """
    Analyze the user story to extract key information.
    
    Args:
        state: Current agent state
        
    Returns:
        AgentState: Updated agent state
    """
    # Extract user story from state
    user_story = state["user_story"]
    
    # Format the similar stories for context
    similar_stories_text = ""
    for i, story in enumerate(state["similar_stories"]):
        similar_stories_text += f"\n--- Similar User Story {i+1} ---\n"
        similar_stories_text += f"Title: {story.title}\n"
        similar_stories_text += f"Description: {story.description}\n"
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content=ANALYZE_USER_STORY_TEMPLATE.format(
            title=user_story.title,
            description=user_story.description,
            similar_stories=similar_stories_text
        ))
    ])
    
    # Get the response from the LLM
    response = model.invoke(
        prompt.invoke({"messages": state["messages"]})
    )
    
    # Try to parse the analysis as JSON
    try:
        analysis = json.loads(response.content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse analysis as JSON: {response.content}")
        analysis = {
            "key_features": [],
            "user_roles": [],
            "acceptance_criteria": [],
            "edge_cases": []
        }
    
    # Add the messages to the state
    messages = state["messages"] + [
        HumanMessage(content=f"Please analyze this user story: {user_story.title}"),
        response
    ]
    
    # Return the updated state
    return {
        **state,
        "messages": messages,
        "analysis": analysis
    }

def generate_test_cases(state: AgentState) -> AgentState:
    """
    Generate test cases based on the analysis.
    
    Args:
        state: Current agent state
        
    Returns:
        AgentState: Updated agent state
    """
    # Extract information from state
    user_story = state["user_story"]
    analysis = state["analysis"]
    
    # Format the similar test cases for context
    similar_test_cases_text = ""
    for i, test_case in enumerate(state["similar_test_cases"]):
        similar_test_cases_text += f"\n--- Similar Test Case {i+1} ---\n"
        similar_test_cases_text += f"Title: {test_case.title}\n"
        similar_test_cases_text += f"Description: {test_case.description}\n"
        similar_test_cases_text += f"Steps:\n"
        
        for j, step in enumerate(test_case.steps, start=1):
            similar_test_cases_text += f"  {j}. {step.get('action', '')}\n"
            similar_test_cases_text += f"     Expected: {step.get('expected', '')}\n"
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
        HumanMessage(content=GENERATE_TEST_CASES_TEMPLATE.format(
            title=user_story.title,
            description=user_story.description,
            key_features=", ".join(analysis.get("key_features", [])),
            user_roles=", ".join(analysis.get("user_roles", [])),
            acceptance_criteria="\n".join([f"- {ac}" for ac in analysis.get("acceptance_criteria", [])]),
            edge_cases="\n".join([f"- {ec}" for ec in analysis.get("edge_cases", [])]),
            similar_test_cases=similar_test_cases_text
        ))
    ])
    
    # Get the response from the LLM
    response = model.invoke(
        prompt.invoke({"messages": state["messages"]})
    )
    
    # Try to parse the test cases as JSON
    try:
        test_cases_json = json.loads(response.content)
        
        # Convert the JSON to TestCaseRecord objects
        test_cases = []
        for tc in test_cases_json:
            test_cases.append(TestCaseRecord(
                story_id=user_story.story_id,
                title=tc.get("title", ""),
                description=tc.get("description", ""),
                steps=tc.get("steps", []),
                test_case_text=tc.get("test_case_text", ""),
                test_case_csv=tc.get("test_case_csv", "")
            ))
    except json.JSONDecodeError:
        logger.error(f"Failed to parse test cases as JSON: {response.content}")
        test_cases = []
    
    # Add the messages to the state
    messages = state["messages"] + [
        HumanMessage(content="Please generate test cases based on the analysis."),
        response
    ]
    
    # Return the updated state
    return {
        **state,
        "messages": messages,
        "test_cases": test_cases
    }

# Define the graph
def create_agent_graph():
    """
    Create the LangGraph agent graph.
    
    Returns:
        StateGraph: The agent graph
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("analyze_user_story", analyze_user_story)
    graph.add_node("generate_test_cases", generate_test_cases)
    
    # Add edges
    graph.add_edge("analyze_user_story", "generate_test_cases")
    graph.add_edge("generate_test_cases", END)
    
    # Set the entry point
    graph.set_entry_point("analyze_user_story")
    
    # Compile the graph
    return graph.compile()

# Create a memory-based checkpoint saver
memory_saver = MemorySaver()

# Create the graph with a memory saver
qa_agent_graph = create_agent_graph()

# Initialize the graph with a checkpoint
qa_agent_app = qa_agent_graph.with_checkpointer(memory_saver)

# Function to process a new user story
async def process_user_story_with_langgraph(
    user_story: UserStoryRecord,
    similar_stories: List[UserStoryRecord],
    similar_test_cases: List[TestCaseRecord]
) -> Tuple[List[TestCaseRecord], str]:
    """
    Process a user story with the LangGraph agent.
    
    Args:
        user_story: The user story to process
        similar_stories: Similar user stories for context
        similar_test_cases: Similar test cases for context
        
    Returns:
        Tuple[List[TestCaseRecord], str]: Generated test cases and summary
    """
    # Initialize the state
    initial_state = AgentState(
        messages=[],
        user_story=user_story,
        similar_stories=similar_stories,
        similar_test_cases=similar_test_cases,
        analysis=None,
        test_cases=[]
    )
    
    # Execute the graph
    for event in qa_agent_app.stream(initial_state):
        if event["event"] == "start":
            logger.info(f"Starting LangGraph agent for user story {user_story.story_id}")
        elif event["event"] == "end":
            final_state = event["state"]
            
            # Extract the test cases
            test_cases = final_state["test_cases"]
            
            # Create a summary
            summary = f"Generated {len(test_cases)} test cases for user story: {user_story.title}"
            
            return test_cases, summary
    
    # If we reached here, something went wrong
    logger.error(f"LangGraph agent did not complete for user story {user_story.story_id}")
    return [], "Error: LangGraph agent did not complete"
