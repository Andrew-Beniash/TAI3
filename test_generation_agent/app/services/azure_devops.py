"""
Azure DevOps service for the QA Agent application.
Handles interactions with Azure DevOps APIs.
"""
import logging
from typing import List, Dict, Any, Optional

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from msrest.exceptions import ClientRequestError

from app.config import AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT
from app.models.data_models import UserStory, TestCase

logger = logging.getLogger(__name__)

class AzureDevOpsService:
    """Service for interacting with Azure DevOps."""
    
    def __init__(self, pat: Optional[str] = None, org: Optional[str] = None, project: Optional[str] = None):
        """
        Initialize the Azure DevOps service.
        
        Args:
            pat: Personal Access Token for Azure DevOps
            org: Azure DevOps organization
            project: Azure DevOps project
        """
        self.pat = pat or AZURE_DEVOPS_PAT
        self.org = org or AZURE_DEVOPS_ORG
        self.project = project or AZURE_DEVOPS_PROJECT
        
        if not all([self.pat, self.org, self.project]):
            logger.warning("Missing Azure DevOps configuration. Some features will be disabled.")
            self.client = None
        else:
            try:
                credentials = BasicAuthentication('', self.pat)
                connection = Connection(base_url=f"https://dev.azure.com/{self.org}", creds=credentials)
                self.client = connection.clients.get_work_item_tracking_client()
                logger.info(f"Connected to Azure DevOps organization: {self.org}, project: {self.project}")
            except Exception as e:
                logger.error(f"Failed to connect to Azure DevOps: {e}")
                self.client = None
    
    def get_user_story(self, work_item_id: str) -> Optional[UserStory]:
        """
        Get a user story from Azure DevOps.
        
        Args:
            work_item_id: The ID of the work item to get
            
        Returns:
            UserStory object or None if not found
        """
        if not self.client:
            logger.error("Azure DevOps client not initialized")
            return None
        
        try:
            work_item = self.client.get_work_item(int(work_item_id), self.project)
            
            # Extract fields from the work item
            fields = work_item.fields
            title = fields.get("System.Title", "")
            description = fields.get("System.Description", "")
            
            return UserStory(
                story_id=str(work_item.id),
                project_id=self.project,
                title=title,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error getting work item {work_item_id}: {e}")
            return None
    
    def create_test_cases(self, test_cases: List[TestCase], parent_id: str) -> List[str]:
        """
        Create test cases in Azure DevOps.
        
        Args:
            test_cases: List of test cases to create
            parent_id: ID of the parent work item (user story)
            
        Returns:
            List of created test case IDs
        """
        if not self.client:
            logger.error("Azure DevOps client not initialized")
            return []
        
        created_ids = []
        
        try:
            for tc in test_cases:
                # Create document for Test Case work item
                document = [
                    {
                        "op": "add",
                        "path": "/fields/System.Title",
                        "value": tc.title
                    },
                    {
                        "op": "add",
                        "path": "/fields/System.Description",
                        "value": tc.description
                    },
                    {
                        "op": "add",
                        "path": "/fields/Microsoft.VSTS.TCM.Steps",
                        "value": tc.test_case_text
                    },
                    {
                        "op": "add",
                        "path": "/fields/System.WorkItemType",
                        "value": "Test Case"
                    },
                    {
                        "op": "add",
                        "path": "/fields/System.State",
                        "value": "Design"
                    }
                ]
                
                # Create the test case
                created_work_item = self.client.create_work_item(
                    document=document,
                    project=self.project,
                    type="Test Case"
                )
                
                # Add relation to parent user story
                if created_work_item and parent_id:
                    self.client.add_relation(
                        work_item_id=created_work_item.id,
                        relation={
                            "rel": "System.LinkTypes.Hierarchy-Reverse",
                            "url": f"https://dev.azure.com/{self.org}/{self.project}/_apis/wit/workItems/{parent_id}"
                        }
                    )
                
                created_ids.append(str(created_work_item.id))
                logger.info(f"Created test case {created_work_item.id} for user story {parent_id}")
            
            return created_ids
            
        except Exception as e:
            logger.error(f"Error creating test cases: {e}")
            return created_ids
