"""
Prompt templates for the LangGraph QA Agent.
These templates are used to guide the LLM in generating test cases.
"""
from langchain_core.prompts import PromptTemplate

CONTEXT_PROMPT = """
# CONTEXT
You are a QA automation expert tasked with designing comprehensive test cases for user stories in a software development project.

## USER STORY DETAILS
{user_story_details}

## SIMILAR USER STORIES & TEST CASES
The following are similar user stories and their test cases from the system that might provide context:

{context_examples}
"""

TEST_CASE_GENERATION_PROMPT = """
# TEST CASE GENERATION TASK
Create a set of detailed test cases for the given user story. Include positive, negative, and edge case scenarios.

{context}

## REQUIREMENTS
1. Generate at least one test case for each of these types:
   - Positive test case: Verifies the functionality works as expected with valid inputs
   - Negative test case: Tests the system's response to invalid inputs or unauthorized actions
   - Edge case: Tests boundary conditions or unusual scenarios

2. For each test case, include:
   - A clear, descriptive title
   - A brief description of what the test is verifying
   - Numbered steps with detailed actions
   - Expected result after following all steps
   - Test type classification (positive, negative, or edge)

3. Format each test case in Markdown with these sections:
   # Test Case Title
   Brief description of the test case
   
   ## Steps
   1. First step
   2. Second step
   3. ...
   
   ## Expected Result
   What should happen

## OUTPUT
Generate at least 3 test cases (1 of each type) and at most 5 total.
Do not include any explanations or additional comments, only output the test cases in the format specified.
"""

RETRIEVE_CONTEXT_PROMPT = """
# CONTEXTUAL SEARCH TASK
Given a user story, search for similar user stories and test cases that could provide useful context for test case generation.

## USER STORY
{user_story}

## TASK
1. Identify key features, functionality, and requirements in this user story
2. Consider what types of test cases would be appropriate (positive, negative, edge cases)
3. Determine what similar past examples would be most helpful

## OUTPUT
Return the search terms and criteria that would help find the most relevant similar user stories and test cases. Format your response as:
```
search_query: <a concise search query>
story_limit: <integer between 2-5>
test_case_limit: <integer between 3-10>
```
"""

FORMAT_TEST_CASES_PROMPT = """
# TEST CASE FORMATTING TASK
Format the generated test cases into both markdown and CSV formats.

## GENERATED TEST CASES
{test_cases}

## TASK
1. Ensure each test case follows the required format
2. Generate both a markdown and CSV representation for each
3. Structure the CSV with columns: Step, Description, Expected Result

## OUTPUT
Return the test cases with both markdown and CSV representations. Each test case should include:
- title
- description
- steps (as a list of step objects)
- expected_result
- test_type
- test_case_text (markdown format)
- test_case_csv (CSV format)
"""

# Create prompt templates
context_prompt_template = PromptTemplate.from_template(CONTEXT_PROMPT)
test_case_generation_template = PromptTemplate.from_template(TEST_CASE_GENERATION_PROMPT)
retrieve_context_template = PromptTemplate.from_template(RETRIEVE_CONTEXT_PROMPT)
format_test_cases_template = PromptTemplate.from_template(FORMAT_TEST_CASES_PROMPT)
