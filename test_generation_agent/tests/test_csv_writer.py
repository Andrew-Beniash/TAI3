"""
Test script for the CSV writer utility.
"""
import sys
import os
from pathlib import Path
import pytest
import csv
import io

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the CSV writer utility
from app.utils.csv_writer import (
    generate_csv_from_test_cases,
    generate_csv_for_single_test_case,
    parse_csv_to_test_case_steps
)

# Import the data models
from app.models.data_models import TestCaseRecord

# Create sample test cases for testing
def create_sample_test_cases():
    """Create sample test cases for testing"""
    test_case1 = TestCaseRecord(
        story_id="123",
        test_case_id="TC-1",
        title="Verify successful login",
        description="Test successful login with valid credentials",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed"},
            {"action": "Enter valid username", "expected": "Username is accepted"},
            {"action": "Enter valid password", "expected": "Password is accepted"},
            {"action": "Click login button", "expected": "User is logged in successfully"}
        ],
        test_case_text="",
        test_case_csv=""
    )
    
    test_case2 = TestCaseRecord(
        story_id="123",
        test_case_id="TC-2",
        title="Verify login with invalid password",
        description="Test login with invalid password",
        steps=[
            {"action": "Navigate to login page", "expected": "Login page is displayed"},
            {"action": "Enter valid username", "expected": "Username is accepted"},
            {"action": "Enter invalid password", "expected": "Password is accepted"},
            {"action": "Click login button", "expected": "Error message is displayed"}
        ],
        test_case_text="",
        test_case_csv=""
    )
    
    return [test_case1, test_case2]

def test_generate_csv_from_test_cases():
    """Test generating CSV from test cases"""
    # Get sample test cases
    test_cases = create_sample_test_cases()
    
    # Generate CSV
    csv_string = generate_csv_from_test_cases(test_cases)
    
    # Check if CSV string is not empty
    assert csv_string
    assert isinstance(csv_string, str)
    
    # Parse the CSV string into rows
    csv_reader = csv.reader(io.StringIO(csv_string))
    rows = list(csv_reader)
    
    # Check the header row
    assert rows[0] == ["ID", "Title", "Description", "Step", "Action", "Expected Result"]
    
    # Check the first test case's first step
    assert rows[1][0] == "TC-1"  # ID
    assert rows[1][1] == "Verify successful login"  # Title
    assert rows[1][2] == "Test successful login with valid credentials"  # Description
    assert rows[1][3] == "1"  # Step number
    assert rows[1][4] == "Navigate to login page"  # Action
    assert rows[1][5] == "Login page is displayed"  # Expected Result
    
    # Check the first test case's subsequent steps (should have empty ID, Title, Description)
    assert rows[2][0] == ""  # ID (empty for subsequent steps)
    assert rows[2][1] == ""  # Title (empty for subsequent steps)
    assert rows[2][2] == ""  # Description (empty for subsequent steps)
    assert rows[2][3] == "2"  # Step number
    
    # Check that we have the right number of rows (header + 8 steps + 1 blank row between test cases)
    assert len(rows) == 10

def test_generate_csv_for_single_test_case():
    """Test generating CSV for a single test case"""
    # Get a sample test case
    test_case = create_sample_test_cases()[0]
    
    # Generate CSV
    csv_string = generate_csv_for_single_test_case(test_case)
    
    # Check if CSV string is not empty
    assert csv_string
    assert isinstance(csv_string, str)
    
    # Parse the CSV string into rows
    csv_reader = csv.reader(io.StringIO(csv_string))
    rows = list(csv_reader)
    
    # Check the header row
    assert rows[0] == ["Action", "Expected Result"]
    
    # Check the steps
    assert rows[1][0] == "Navigate to login page"  # Action
    assert rows[1][1] == "Login page is displayed"  # Expected Result
    
    # Check that we have the right number of rows (header + 4 steps)
    assert len(rows) == 5

def test_parse_csv_to_test_case_steps():
    """Test parsing CSV to test case steps"""
    # Sample CSV string
    csv_string = "Action,Expected Result\nNavigate to login page,Login page is displayed\nEnter valid username,Username is accepted"
    
    # Parse CSV to steps
    steps = parse_csv_to_test_case_steps(csv_string)
    
    # Check if steps is a list of dictionaries
    assert isinstance(steps, list)
    assert len(steps) == 2
    assert all(isinstance(step, dict) for step in steps)
    
    # Check the steps
    assert steps[0]["action"] == "Navigate to login page"
    assert steps[0]["expected"] == "Login page is displayed"
    assert steps[1]["action"] == "Enter valid username"
    assert steps[1]["expected"] == "Username is accepted"

def test_parse_csv_to_test_case_steps_empty_csv():
    """Test parsing empty CSV to test case steps"""
    # Test with empty CSV
    steps = parse_csv_to_test_case_steps("")
    assert steps == []

def test_generate_csv_from_test_cases_empty_list():
    """Test generating CSV from empty test cases list"""
    # Test with empty list
    csv_string = generate_csv_from_test_cases([])
    assert csv_string == ""

if __name__ == "__main__":
    # Run the tests manually with pytest
    pytest.main(["-xvs", __file__])
