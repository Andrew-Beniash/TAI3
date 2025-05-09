"""
Azure DevOps integration service.
Handles interactions with Azure DevOps API for retrieving user stories and creating test cases.
"""
import logging
import base64
from typing import Dict, Any, List, Optional
import asyncio
import re

from app.config import get_azure_devops_credentials
from app.models.data_models import TestCaseRecord

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Azure DevOps client
try:
    from azure.devops.connection import Connection
    from azure.devops.v6_0.work_item_tracking import WorkItemTrackingClient
    from azure.devops.v6_0.test import TestClient
    from msrest.authentication import BasicAuthentication
    
    # Get Azure DevOps credentials
    credentials = get_azure_devops_credentials()
    
    # Set up authentication
    personal_access_token = credentials.get("personal_access_token", "")
    organization_url = f"https://dev.azure.com/{credentials.get('organization', '')}"
    project = credentials.get("project", "")
    
    # Check if credentials are configured
    if personal_access_token and organization_url != "https://dev.azure.com/":
        # Create a connection to Azure DevOps
        credentials = BasicAuthentication('', personal_access_token)
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get clients
        work_item_client = connection.clients.get_work_item_tracking_client()
        test_client = connection.clients.get_test_client()
        
        logger.info(f"Azure DevOps clients initialized for organization: {credentials.get('organization', '')}")
    else:
        logger.warning("Azure DevOps credentials not configured. Integration will not be available.")
        work_item_client = None
        test_client = None
        
except ImportError:
    logger.error("Azure DevOps SDK not installed. Please install with 'pip install azure-devops'")
    work_item_client = None
    test_client = None
except Exception as e:
    logger.error(f"Error initializing Azure DevOps client: {e}", exc_info=True)
    work_item_client = None
    test_client = None

async def get_user_story(story_id: str) -> Dict[str, Any]:
    """
    Get a user story from Azure DevOps.
    
    Args:
        story_id: The ID of the user story
        
    Returns:
        Dict[str, Any]: The user story data
    """
    if not work_item_client:
        logger.error("Azure DevOps client not initialized")
        return {}
        
    try:
        # Run the operation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        work_item = await loop.run_in_executor(
            None, 
            lambda: work_item_client.get_work_item(int(story_id))
        )
        
        # Extract the relevant fields
        return {
            "id": work_item.id,
            "title": work_item.fields.get("System.Title", ""),
            "description": work_item.fields.get("System.Description", ""),
            "state": work_item.fields.get("System.State", ""),
            "created_by": work_item.fields.get("System.CreatedBy", ""),
            "created_date": work_item.fields.get("System.CreatedDate", ""),
            "work_item_type": work_item.fields.get("System.WorkItemType", "")
        }
    except Exception as e:
        logger.error(f"Error getting user story {story_id}: {e}", exc_info=True)
        return {}

async def create_test_cases_in_azure_devops(
    story_id: str, 
    test_cases: List[TestCaseRecord]
) -> Dict[str, Any]:
    """
    Create test cases in Azure DevOps and link them to the user story.
    
    Args:
        story_id: The ID of the user story
        test_cases: List of test cases to create
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    if not work_item_client:
        logger.error("Azure DevOps client not initialized")
        return {"error": "Azure DevOps client not initialized"}
        
    if not test_cases:
        logger.warning("No test cases to create")
        return {"created_test_cases": 0, "test_case_ids": []}
        
    try:
        created_test_cases = []
        
        # Get Azure DevOps project and credentials
        credentials = get_azure_devops_credentials()
        project = credentials.get("project", "")
        
        # Create each test case
        for test_case in test_cases:
            # Prepare the fields for the test case
            fields = {
                "System.Title": test_case.title,
                "System.Description": test_case.description,
                "System.WorkItemType": "Test Case",
                "System.Tags": "generated,ai",
                "Microsoft.VSTS.TCM.Steps": _format_steps_for_azure_devops(test_case.steps)
            }
            
            # Create the test case
            loop = asyncio.get_event_loop()
            test_case_work_item = await loop.run_in_executor(
                None,
                lambda: work_item_client.create_work_item(
                    document=[
                        {"op": "add", "path": f"/fields/{field}", "value": value}
                        for field, value in fields.items()
                    ],
                    project=project,
                    type="Test Case"
                )
            )
            
            # Link the test case to the user story
            if test_case_work_item and test_case_work_item.id:
                # Create a link from the test case to the user story
                await loop.run_in_executor(
                    None,
                    lambda: work_item_client.add_link(
                        link_type_name="Tests",
                        source_id=test_case_work_item.id,
                        target_id=int(story_id)
                    )
                )
                
                # Update the test case record with the Azure DevOps ID
                test_case.test_case_id = str(test_case_work_item.id)
                created_test_cases.append(test_case_work_item.id)
                
                logger.info(f"Created test case {test_case_work_item.id}: {test_case.title}")
        
        return {
            "created_test_cases": len(created_test_cases),
            "test_case_ids": created_test_cases
        }
    except Exception as e:
        logger.error(f"Error creating test cases: {e}", exc_info=True)
        return {"error": str(e)}

def _format_steps_for_azure_devops(steps: List[Dict[str, str]]) -> str:
    """
    Format test case steps for Azure DevOps.
    
    Args:
        steps: List of steps with action and expected result
        
    Returns:
        str: Formatted steps in Azure DevOps format
    """
    if not steps:
        return ""
        
    # Format the steps as an HTML table for Azure DevOps
    steps_html = "<steps id='0'><step id='1' type='ActionStep'>"
    
    for i, step in enumerate(steps, start=1):
        action = step.get("action", "")
        expected = step.get("expected", "")
        
        steps_html += f"""
        <parameterizedString isformatted="true">
            <text>{action}</text>
        </parameterizedString>
        <parameterizedString isformatted="true">
            <text>{expected}</text>
        </parameterizedString>
        """
        
        # Add next step marker if not the last step
        if i < len(steps):
            steps_html += f"</step><step id='{i+1}' type='ActionStep'>"
    
    steps_html += "</step></steps>"
    
    return steps_html

async def add_comment_to_user_story(story_id: str, comment: str) -> bool:
    """
    Add a comment to a user story in Azure DevOps.
    
    Args:
        story_id: The ID of the user story
        comment: The comment text
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not work_item_client:
        logger.error("Azure DevOps client not initialized")
        return False
        
    try:
        # Get Azure DevOps project and credentials
        credentials = get_azure_devops_credentials()
        project = credentials.get("project", "")
        
        # Add the comment
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: work_item_client.add_comment(
                project=project,
                work_item_id=int(story_id),
                comment=comment
            )
        )
        
        logger.info(f"Added comment to user story {story_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding comment to user story {story_id}: {e}", exc_info=True)
        return False

async def mock_create_test_cases(
    story_id: str, 
    test_cases: List[TestCaseRecord]
) -> Dict[str, Any]:
    """
    Mock function to simulate creation of test cases in Azure DevOps.
    Used for local development and testing when Azure DevOps is not available.
    
    Args:
        story_id: The ID of the user story
        test_cases: List of test cases to create
        
    Returns:
        Dict[str, Any]: Mock result of the operation
    """
    # Simulate some processing time
    await asyncio.sleep(0.5)
    
    # Generate mock IDs for the test cases
    test_case_ids = []
    for i, test_case in enumerate(test_cases):
        # Generate a mock ID
        mock_id = f"TC-{story_id}-{i+1}"
        test_case.test_case_id = mock_id
        test_case_ids.append(mock_id)
        
        logger.info(f"[MOCK] Created test case {mock_id}: {test_case.title}")
    
    return {
        "created_test_cases": len(test_cases),
        "test_case_ids": test_case_ids
    }
