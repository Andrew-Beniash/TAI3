import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import csv
import io

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# Initialize model
model = ChatOpenAI(api_key=openai_key, model="gpt-4")

# Memory setup
memory = SqliteSaver.from_conn_string(":memory:")

# Agent state definition
class AgentState(TypedDict):
    user_story: str
    extracted_requirements: str
    test_scenarios: str
    test_cases: str
    feedback: str
    revision_number: int
    max_revisions: int
    test_cases_csv: str

# Prompts
REQUIREMENT_EXTRACTION_PROMPT = """
You are a senior QA engineer. Given the following user story, extract key functional and non-functional requirements.
"""

TEST_SCENARIO_GENERATION_PROMPT = """
You are a QA strategist. Based on the extracted requirements, generate a list of test scenarios that include standard, edge, and negative paths.
"""

TEST_CASE_GENERATION_PROMPT = """
You are an experienced QA test writer. Write detailed test cases for each scenario including title, objective, preconditions, steps, expected results, and test type (positive/negative/edge).
Return the output in CSV format with the following columns:
Title, Objective, Preconditions, Steps, Expected Result, Test Type
"""

FEEDBACK_PROMPT = """
You are a QA reviewer. Provide feedback on the generated test cases. Identify any missing scenarios, redundancy, or opportunities to improve clarity or coverage.
"""

# Nodes
def extract_requirements_node(state: AgentState):
    messages = [
        SystemMessage(content=REQUIREMENT_EXTRACTION_PROMPT),
        HumanMessage(content=state["user_story"]),
    ]
    response = model.invoke(messages)
    return {"extracted_requirements": response.content}

def generate_test_scenarios_node(state: AgentState):
    messages = [
        SystemMessage(content=TEST_SCENARIO_GENERATION_PROMPT),
        HumanMessage(content=state["extracted_requirements"]),
    ]
    response = model.invoke(messages)
    return {"test_scenarios": response.content}

def generate_test_cases_node(state: AgentState):
    messages = [
        SystemMessage(content=TEST_CASE_GENERATION_PROMPT),
        HumanMessage(content=state["test_scenarios"]),
    ]
    response = model.invoke(messages)
    test_cases_csv = response.content.strip()
    return {
        "test_cases": test_cases_csv,
        "test_cases_csv": test_cases_csv,
        "revision_number": state.get("revision_number", 1) + 1,
    }

def collect_feedback_node(state: AgentState):
    messages = [
        SystemMessage(content=FEEDBACK_PROMPT),
        HumanMessage(content=state["test_cases"]),
    ]
    response = model.invoke(messages)
    return {"feedback": response.content}

def apply_feedback_node(state: AgentState):
    messages = [
        SystemMessage(content=TEST_CASE_GENERATION_PROMPT),
        HumanMessage(content=f"Previous Test Cases:\n{state['test_cases']}\n\nFeedback:\n{state['feedback']}"),
    ]
    response = model.invoke(messages)
    test_cases_csv = response.content.strip()
    return {
        "test_cases": test_cases_csv,
        "test_cases_csv": test_cases_csv,
        "revision_number": state["revision_number"] + 1,
    }

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "collect_feedback"

# Graph construction
builder = StateGraph(AgentState)

builder.add_node("extract_requirements", extract_requirements_node)
builder.add_node("generate_test_scenarios", generate_test_scenarios_node)
builder.add_node("generate_test_cases", generate_test_cases_node)
builder.add_node("collect_feedback", collect_feedback_node)
builder.add_node("apply_feedback", apply_feedback_node)

builder.set_entry_point("extract_requirements")

builder.add_edge("extract_requirements", "generate_test_scenarios")
builder.add_edge("generate_test_scenarios", "generate_test_cases")
builder.add_conditional_edges("generate_test_cases", should_continue, {END: END, "collect_feedback": "collect_feedback"})
builder.add_edge("collect_feedback", "apply_feedback")
builder.add_edge("apply_feedback", "generate_test_cases")

# Compile the graph
graph = builder.compile(checkpointer=memory)

# Example invocation (console testing)
# if __name__ == "__main__":
#     initial_state = {
#         "user_story": "As a user, I want to reset my password so that I can regain access to my account.",
#         "max_revisions": 2,
#         "revision_number": 1,
#     }
#     for state in graph.stream(initial_state, {"configurable": {"thread_id": "1"}}):
#         print(state)
#         if "test_cases_csv" in state:
#             with open("generated_test_cases.csv", "w", newline="") as f:
#                 f.write(state["test_cases_csv"])
#             print("CSV file saved: generated_test_cases.csv")
