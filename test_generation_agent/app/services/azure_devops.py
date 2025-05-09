"""
Azure DevOps service integration.
Handles communication with Azure DevOps APIs for test case creation and linking.
"""
import logging
import base64
import requests
from typing import Dict, List, Optional, Any, Union

from ..config import (
    AZURE_DEVOPS_ORG,
    AZURE_DEVOPS_PROJECT,
    AZURE_DEVOPS_PAT,
    AZURE_DEVOPS_API_VERSION
)
from ..models.data_models import TestCaseRecord

logger = logging.getLogger(__name__)

class AzureDevOpsService:
    """Service class for interacting with Azure DevOps APIs."""
    
    def __init__(self, org=None, project=None, pat=None, api_version=None):
        """Initialize the Azure DevOps service.
        
        Args:
            org: Azure DevOps organization name
            project: Azure DevOps project name
            pat: Personal Access Token
            api_version: API version to use
        """
        self.org = org or AZURE_DEVOPS_ORG
        self.project = project or AZURE_DEVOPS_PROJECT
        self.pat = pat or AZURE_DEVOPS_PAT
        self.api_version = api_version or AZURE_DEVOPS_API_VERSION
        
        if not all([self.org, self.project, self.pat]):
            logger.error("Azure DevOps configuration is incomplete")
            raise ValueError("Azure DevOps configuration is incomplete. Check org, project, and PAT.")
        
        # Base URLs for different Azure DevOps APIs
        self.base_url = f"https://dev.azure.com/{self.org}/{self.project}"
        self.work_item_url = f"{self.base_url}/_apis/wit/workitems"
        self.test_plans_url = f"{self.base_url}/_apis/test/plans"
        
        # Create Authorization header using Personal Access Token
        self.auth_header = self._create_auth_header(self.pat)
    
    def _create_auth_header(self, pat: str) -> Dict[str, str]:
        """Create the authorization header for Azure DevOps API.
        
        Args:
            pat: Personal Access Token
            
        Returns:
            Dictionary containing the authorization header
        """
        encoded_pat = base64.b64encode(f":{pat}".encode()).decode()
        return {
            "Authorization": f"Basic {encoded_pat}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, url: str, params: Dict = None, json_data: Dict = None) -> Dict:
        """Make a request to the Azure DevOps API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: API endpoint URL
            params: Query parameters
            json_data: JSON data for POST/PATCH requests
            
        Returns:
            JSON response from the API
        """
        # Add API version to parameters
        if params is None:
            params = {}
        params["api-version"] = self.api_version
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.auth_header,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Azure DevOps API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_work_item(self, work_item_id: int) -> Dict:
        """Get a work item by ID.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            Work item details
        """
        url = f"{self.work_item_url}/{work_item_id}"
        return self._make_request("GET", url)
    
    def create_test_plan(self, name: str, description: str = "") -> Dict:
        """Create a test plan.
        
        Args:
            name: Name of the test plan
            description: Description of the test plan
            
        Returns:
            Created test plan details
        """
        data = {
            "name": name,
            "description": description
        }
        return self._make_request("POST", self.test_plans_url, json_data=data)
    
    def create_test_suite(self, plan_id: int, name: str, suite_type: str = "staticTestSuite") -> Dict:
        """Create a test suite within a test plan.
        
        Args:
            plan_id: ID of the test plan
            name: Name of the test suite
            suite_type: Type of test suite (default: staticTestSuite)
            
        Returns:
            Created test suite details
        """
        url = f"{self.test_plans_url}/{plan_id}/suites"
        data = {
            "name": name,
            "suiteType": suite_type
        }
        return self._make_request("POST", url, json_data=data)
    
    def create_test_case(self, test_case: TestCaseRecord) -> Dict:
        """Create a test case work item.
        
        Args:
            test_case: Test case record to create
            
        Returns:
            Created test case work item details
        """
        # First create the test case as a work item
        url = f"{self.work_item_url}/$Microsoft.TestCase"
        
        # Prepare operations for the work item creation
        operations = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": test_case.title
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": test_case.description
            },
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.TCM.Steps",
                "value": self._format_test_steps(test_case.steps)
            }
        ]
        
        work_item = self._make_request("PATCH", url, json_data=operations)
        logger.info(f"Created test case work item with ID: {work_item.get('id')}")
        
        return work_item
    
    def _format_test_steps(self, steps: List[Dict[str, str]]) -> str:
        """Format test steps into the Azure DevOps XML format.
        
        Args:
            steps: List of test steps with action and expected result
            
        Returns:
            Formatted XML string for test steps
        """
        # XML template for test steps
        steps_xml = '<steps id="0" last="2">'
        
        for i, step in enumerate(steps, start=1):
            action = step.get('action', '')
            expected = step.get('expected', '')
            
            step_xml = f"""
            <step id="{i}" type="ActionStep">
                <parameterizedString isformatted="true">{action}</parameterizedString>
                <parameterizedString isformatted="true">{expected}</parameterizedString>
            </step>
            """
            steps_xml += step_xml
        
        steps_xml += '</steps>'
        return steps_xml
    
    def add_test_case_to_suite(self, plan_id: int, suite_id: int, test_case_id: int) -> Dict:
        """Add a test case to a test suite.
        
        Args:
            plan_id: ID of the test plan
            suite_id: ID of the test suite
            test_case_id: ID of the test case
            
        Returns:
            Result of adding the test case to the suite
        """
        url = f"{self.test_plans_url}/{plan_id}/suites/{suite_id}/testcases/{test_case_id}"
        return self._make_request("POST", url)
    
    def link_work_items(self, source_id: int, target_id: int, link_type: str = "Microsoft.VSTS.Common.TestedBy-Forward") -> Dict:
        """Link two work items together.
        
        Args:
            source_id: ID of the source work item (e.g., user story)
            target_id: ID of the target work item (e.g., test case)
            link_type: Type of link relationship
            
        Returns:
            Result of linking the work items
        """
        url = f"{self.work_item_url}/{source_id}"
        
        operations = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": link_type,
                    "url": f"{self.work_item_url}/{target_id}"
                }
            }
        ]
        
        return self._make_request("PATCH", url, json_data=operations)
    
    def create_test_cases_for_story(self, story_id: int, test_cases: List[TestCaseRecord], 
                                    plan_name: str = None, suite_name: str = None) -> List[Dict]:
        """Create test cases for a user story and link them together.
        
        Args:
            story_id: ID of the user story
            test_cases: List of test case records to create
            plan_name: Name of the test plan to create or use
            suite_name: Name of the test suite to create or use
            
        Returns:
            List of created test cases
        """
        try:
            # Get user story details
            story = self.get_work_item(story_id)
            story_title = story.get('fields', {}).get('System.Title', 'User Story')
            
            # Create or use test plan
            plan_name = plan_name or f"Test Plan for {story_title}"
            plan = self.create_test_plan(plan_name, f"Test plan for user story: {story_title}")
            plan_id = plan.get('id')
            
            # Create or use test suite
            suite_name = suite_name or f"Test Suite for {story_title}"
            suite = self.create_test_suite(plan_id, suite_name)
            suite_id = suite.get('id')
            
            created_test_cases = []
            
            # Create test cases and add them to the suite
            for test_case in test_cases:
                # Create test case work item
                work_item = self.create_test_case(test_case)
                test_case_id = work_item.get('id')
                
                # Add test case to suite
                self.add_test_case_to_suite(plan_id, suite_id, test_case_id)
                
                # Link test case to user story
                self.link_work_items(story_id, test_case_id)
                
                # Update test case record with Azure DevOps ID
                test_case.test_case_id = str(test_case_id)
                created_test_cases.append(work_item)
                
                logger.info(f"Created test case {test_case_id} and linked to story {story_id}")
            
            return created_test_cases
        
        except Exception as e:
            logger.error(f"Error creating test cases for story {story_id}: {e}")
            raise
