"""
Prompt templates for the LangGraph agent's nodes.
"""

# System prompt for the agent
SYSTEM_PROMPT = """
You are an expert QA test engineer specializing in generating comprehensive test cases from user stories.
Your goal is to analyze user stories and create detailed, thorough test cases that cover both happy paths
and edge cases to ensure robust testing coverage.

For each test case, you should include:
- A clear, descriptive title
- A detailed description of what is being tested
- Step-by-step actions with expected results
- Both positive scenarios (happy paths) and negative scenarios (error conditions)
- Edge cases that might not be obvious

You should always output the test cases in a structured JSON format that is compatible with Azure DevOps.
"""

# Template for presenting a user story
USER_STORY_TEMPLATE = """
# User Story:
Title: {title}

Description:
{description}

"""

# Template for analyzing a user story
ANALYZE_USER_STORY_TEMPLATE = """
# User Story Analysis Task

Analyze the following user story and extract key information that would be useful for generating test cases:

## User Story
Title: {title}

Description:
{description}

{similar_stories}

Your task is to extract and organize the following information from this user story:
1. Key features or functionalities mentioned
2. User roles or personas involved
3. Explicit and implicit acceptance criteria
4. Potential edge cases or error conditions

Return your analysis in the following JSON format:
```json
{{
  "key_features": ["feature1", "feature2", ...],
  "user_roles": ["role1", "role2", ...],
  "acceptance_criteria": ["criterion1", "criterion2", ...],
  "edge_cases": ["edge case1", "edge case2", ...]
}}
```
"""

# Template for generating test cases
GENERATE_TEST_CASES_TEMPLATE = """
# Test Case Generation Task

Using the analysis of the user story, generate a comprehensive set of test cases.

## User Story
Title: {title}

Description:
{description}

## Analysis
Key Features: {key_features}
User Roles: {user_roles}
Acceptance Criteria:
{acceptance_criteria}
Edge Cases:
{edge_cases}

## Similar Test Cases (for reference)
{similar_test_cases}

Your task is to generate detailed test cases that cover happy paths, error conditions, and edge cases.

For each test case, include:
1. A clear title
2. A description of what is being tested
3. Detailed steps with expected results

Return your test cases in the following JSON format:
```json
[
  {{
    "title": "Test Case Title",
    "description": "Detailed description of what this test case verifies",
    "steps": [
      {{
        "action": "Step 1 action description",
        "expected": "Expected result for step 1"
      }},
      {{
        "action": "Step 2 action description",
        "expected": "Expected result for step 2"
      }}
    ],
    "test_case_text": "Markdown formatted test case for human readability",
    "test_case_csv": "CSV formatted test case for export"
  }},
  ... additional test cases ...
]
```

Generate at least 3-5 test cases that provide thorough coverage of the functionality, including positive scenarios, negative scenarios, and edge cases.
"""

# Template for formatting a test case in markdown
TEST_CASE_MARKDOWN_TEMPLATE = """
# {title}

## Description
{description}

## Steps
{steps}
"""

# Template for formatting test case steps in markdown
TEST_CASE_STEP_MARKDOWN_TEMPLATE = """
{step_number}. {action}
   - Expected: {expected}
"""

# Template for summarizing test case generation
SUMMARY_TEMPLATE = """
# Test Case Generation Summary

User Story: {title}

Generated {test_case_count} test cases:
{test_case_list}

Test cases have been created in Azure DevOps and linked to the user story.
"""
