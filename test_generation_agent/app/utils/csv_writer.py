"""
CSV generation utility for test cases.
"""
import csv
import io
from typing import List, Dict, Any

from app.models.data_models import TestCaseRecord

def generate_csv_from_test_cases(test_cases: List[TestCaseRecord]) -> str:
    """
    Generate a CSV string from a list of test cases.
    
    Args:
        test_cases: List of test cases
        
    Returns:
        str: CSV string
    """
    if not test_cases:
        return ""
    
    # Create a string buffer for the CSV output
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(["ID", "Title", "Description", "Step", "Action", "Expected Result"])
    
    # Write test case rows
    for test_case in test_cases:
        for i, step in enumerate(test_case.steps, start=1):
            # For the first step of each test case, include the test case info
            if i == 1:
                writer.writerow([
                    test_case.test_case_id or "",
                    test_case.title,
                    test_case.description,
                    i,
                    step.get("action", ""),
                    step.get("expected", "")
                ])
            else:
                # For subsequent steps, only include step info
                writer.writerow([
                    "",
                    "",
                    "",
                    i,
                    step.get("action", ""),
                    step.get("expected", "")
                ])
        
        # Add a blank row between test cases
        if test_case != test_cases[-1]:
            writer.writerow(["", "", "", "", "", ""])
    
    # Get the CSV string
    csv_string = output.getvalue()
    output.close()
    
    return csv_string

def generate_csv_for_single_test_case(test_case: TestCaseRecord) -> str:
    """
    Generate a CSV string for a single test case.
    
    Args:
        test_case: The test case
        
    Returns:
        str: CSV string
    """
    # Create a string buffer for the CSV output
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow(["Action", "Expected Result"])
    
    # Write step rows
    for step in test_case.steps:
        writer.writerow([step.get("action", ""), step.get("expected", "")])
    
    # Get the CSV string
    csv_string = output.getvalue()
    output.close()
    
    return csv_string

def parse_csv_to_test_case_steps(csv_string: str) -> List[Dict[str, str]]:
    """
    Parse a CSV string to test case steps.
    
    Args:
        csv_string: CSV string
        
    Returns:
        List[Dict[str, str]]: List of steps
    """
    if not csv_string:
        return []
    
    # Create a CSV reader from the string
    reader = csv.reader(io.StringIO(csv_string))
    
    # Skip the header row
    next(reader, None)
    
    # Parse the steps
    steps = []
    for row in reader:
        if len(row) >= 2:
            steps.append({
                "action": row[0].strip(),
                "expected": row[1].strip()
            })
    
    return steps
