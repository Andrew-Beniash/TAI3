"""
CSV Writer utility for the QA Agent application.
Converts test case steps to CSV format for easier import into test management tools.
"""
import csv
import io
from typing import List, Dict, Any, Optional

def test_case_to_csv(test_case: Dict[str, Any]) -> str:
    """
    Convert a test case to CSV format.
    
    Args:
        test_case: Dictionary containing test case details
        
    Returns:
        String containing CSV data
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(["Step", "Description", "Expected Result"])
    
    # Write steps
    for i, step in enumerate(test_case["steps"], 1):
        # For all steps except the last one, expected result is empty
        if i < len(test_case["steps"]):
            writer.writerow([step["step"], step["description"], ""])
        else:
            # For the last step, include the expected result
            writer.writerow([step["step"], step["description"], test_case["expected_result"]])
    
    return output.getvalue()

def test_cases_to_csv(test_cases: List[Dict[str, Any]]) -> str:
    """
    Convert multiple test cases to a single CSV file.
    
    Args:
        test_cases: List of dictionaries containing test case details
        
    Returns:
        String containing CSV data for all test cases
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(["Test Case ID", "Title", "Type", "Description", "Step", "Step Description", "Expected Result"])
    
    # Write test cases
    for i, tc in enumerate(test_cases, 1):
        test_id = tc.get("test_id", f"TC{i}")
        
        # Write each step as a separate row
        for j, step in enumerate(tc["steps"], 1):
            # Only include title, type, and description in the first row of each test case
            if j == 1:
                title = tc["title"]
                test_type = tc.get("test_type", "")
                description = tc["description"]
            else:
                title = ""
                test_type = ""
                description = ""
            
            # Expected result only in the last step
            expected_result = tc["expected_result"] if j == len(tc["steps"]) else ""
            
            writer.writerow([
                test_id,
                title,
                test_type,
                description,
                step["step"],
                step["description"],
                expected_result
            ])
    
    return output.getvalue()

def markdown_to_test_case(markdown_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a markdown representation of a test case into a structured format.
    
    Args:
        markdown_text: Markdown text representing a test case
        
    Returns:
        Dictionary containing parsed test case or None if parsing fails
    """
    try:
        lines = markdown_text.strip().split('\n')
        
        # Extract title from first line (assumes it's a heading)
        title = lines[0].lstrip('#').strip()
        
        # Find description (assumes it's between title and steps)
        description = ""
        steps_start_index = -1
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip().lower().startswith(('## steps', '## test steps', '# steps', '# test steps')):
                steps_start_index = i
                break
            description += line.strip() + " "
        
        description = description.strip()
        
        if steps_start_index == -1:
            # If steps section not found, look for numbered steps
            for i, line in enumerate(lines[1:], 1):
                if line.strip().startswith('1.'):
                    steps_start_index = i
                    break
        
        if steps_start_index == -1:
            return None
        
        # Extract steps
        steps = []
        expected_result = ""
        expected_result_found = False
        
        for i, line in enumerate(lines[steps_start_index:], steps_start_index):
            line = line.strip()
            
            # Skip empty lines and headings
            if not line or line.startswith('#'):
                continue
            
            # Check if we've reached the expected result section
            if line.lower().startswith(('## expected', '# expected', 'expected result')):
                expected_result_found = True
                continue
            
            if expected_result_found:
                expected_result += line + " "
            else:
                # Parse step (assumes format like "1. Do something")
                step_parts = line.split('.', 1)
                if len(step_parts) == 2 and step_parts[0].strip().isdigit():
                    step_num = step_parts[0].strip()
                    step_desc = step_parts[1].strip()
                    steps.append({"step": step_num, "description": step_desc})
        
        expected_result = expected_result.strip()
        
        # If expected result was not found in a dedicated section, use the last step
        if not expected_result and steps:
            last_step = steps.pop()
            expected_result = last_step["description"]
        
        # Determine test type based on title or description
        test_type = "positive"  # Default
        text_to_check = (title + " " + description).lower()
        
        if any(term in text_to_check for term in ["negative", "invalid", "error", "fail", "reject"]):
            test_type = "negative"
        elif any(term in text_to_check for term in ["edge", "boundary", "limit", "max", "min"]):
            test_type = "edge"
        
        return {
            "title": title,
            "description": description,
            "steps": steps,
            "expected_result": expected_result,
            "test_type": test_type,
            "test_case_text": markdown_text
        }
    
    except Exception as e:
        print(f"Error parsing markdown: {e}")
        return None
