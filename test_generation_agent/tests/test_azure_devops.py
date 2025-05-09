"""
Unit tests for the Azure DevOps service.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from app.services.azure_devops import AzureDevOpsService
from app.models.data_models import TestCaseRecord

class TestAzureDevOpsService(unittest.TestCase):
    """Tests for the AzureDevOpsService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'AZURE_DEVOPS_ORG': 'test-org',
            'AZURE_DEVOPS_PROJECT': 'test-project',
            'AZURE_DEVOPS_PAT': 'test-pat',
            'AZURE_DEVOPS_API_VERSION': '7.0'
        })
        self.env_patcher.start()
        
        # Create the service
        self.service = AzureDevOpsService()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
    
    def test_initialization(self):
        """Test that the service initializes correctly."""
        self.assertEqual(self.service.org, 'test-org')
        self.assertEqual(self.service.project, 'test-project')
        self.assertEqual(self.service.pat, 'test-pat')
        self.assertEqual(self.service.api_version, '7.0')
        
        # Check base URLs
        self.assertEqual(self.service.base_url, 'https://dev.azure.com/test-org/test-project')
        self.assertEqual(self.service.work_item_url, 'https://dev.azure.com/test-org/test-project/_apis/wit/workitems')
        self.assertEqual(self.service.test_plans_url, 'https://dev.azure.com/test-org/test-project/_apis/test/plans')
    
    def test_create_auth_header(self):
        """Test that the authorization header is created correctly."""
        headers = self.service._create_auth_header('test-pat')
        
        # Check that the header contains the expected content
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Basic '))
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    @patch('requests.request')
    def test_make_request(self, mock_request):
        """Test that requests are made correctly."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 123, 'name': 'Test Item'}
        mock_request.return_value = mock_response
        
        # Make a request
        result = self.service._make_request('GET', 'https://example.com/api', {'param': 'value'})
        
        # Check that the request was made with the correct parameters
        mock_request.assert_called_once_with(
            method='GET',
            url='https://example.com/api',
            headers=self.service.auth_header,
            params={'param': 'value', 'api-version': '7.0'},
            json=None
        )
        
        # Check that the response was returned correctly
        self.assertEqual(result, {'id': 123, 'name': 'Test Item'})
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_get_work_item(self, mock_make_request):
        """Test getting a work item."""
        # Mock response
        mock_make_request.return_value = {'id': 123, 'fields': {'System.Title': 'Test Work Item'}}
        
        # Get a work item
        result = self.service.get_work_item(123)
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once_with(
            'GET',
            'https://dev.azure.com/test-org/test-project/_apis/wit/workitems/123'
        )
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['fields']['System.Title'], 'Test Work Item')
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_create_test_plan(self, mock_make_request):
        """Test creating a test plan."""
        # Mock response
        mock_make_request.return_value = {'id': 456, 'name': 'Test Plan'}
        
        # Create a test plan
        result = self.service.create_test_plan('Test Plan', 'Test plan description')
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once_with(
            'POST',
            'https://dev.azure.com/test-org/test-project/_apis/test/plans',
            json_data={'name': 'Test Plan', 'description': 'Test plan description'}
        )
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 456)
        self.assertEqual(result['name'], 'Test Plan')
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_create_test_suite(self, mock_make_request):
        """Test creating a test suite."""
        # Mock response
        mock_make_request.return_value = {'id': 789, 'name': 'Test Suite'}
        
        # Create a test suite
        result = self.service.create_test_suite(456, 'Test Suite')
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once_with(
            'POST',
            'https://dev.azure.com/test-org/test-project/_apis/test/plans/456/suites',
            json_data={'name': 'Test Suite', 'suiteType': 'staticTestSuite'}
        )
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 789)
        self.assertEqual(result['name'], 'Test Suite')
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_create_test_case(self, mock_make_request):
        """Test creating a test case."""
        # Mock response
        mock_make_request.return_value = {'id': 101, 'url': 'https://dev.azure.com/test-org/test-project/_apis/wit/workItems/101'}
        
        # Create a test case
        test_case = TestCaseRecord(
            story_id='123',
            title='Test Case Title',
            description='Test case description',
            steps=[
                {'action': 'Step 1', 'expected': 'Expected Result 1'},
                {'action': 'Step 2', 'expected': 'Expected Result 2'}
            ],
            test_case_text='# Test Case Title\n\nTest case description'
        )
        
        result = self.service.create_test_case(test_case)
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        
        self.assertEqual(args[0], 'PATCH')
        self.assertEqual(args[1], 'https://dev.azure.com/test-org/test-project/_apis/wit/workitems/$Microsoft.TestCase')
        
        # Check operations in the request JSON
        operations = kwargs['json_data']
        self.assertEqual(len(operations), 3)  # Title, Description, Steps
        
        # Check that the title and description are set correctly
        title_op = next(op for op in operations if op['path'] == '/fields/System.Title')
        self.assertEqual(title_op['value'], 'Test Case Title')
        
        desc_op = next(op for op in operations if op['path'] == '/fields/System.Description')
        self.assertEqual(desc_op['value'], 'Test case description')
        
        # Check that the steps are formatted correctly
        steps_op = next(op for op in operations if op['path'] == '/fields/Microsoft.VSTS.TCM.Steps')
        self.assertIn('<steps id="0" last="2">', steps_op['value'])
        self.assertIn('Step 1', steps_op['value'])
        self.assertIn('Expected Result 1', steps_op['value'])
        self.assertIn('Step 2', steps_op['value'])
        self.assertIn('Expected Result 2', steps_op['value'])
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 101)
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_add_test_case_to_suite(self, mock_make_request):
        """Test adding a test case to a test suite."""
        # Mock response
        mock_make_request.return_value = {'id': 101}
        
        # Add test case to suite
        result = self.service.add_test_case_to_suite(456, 789, 101)
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once_with(
            'POST',
            'https://dev.azure.com/test-org/test-project/_apis/test/plans/456/suites/789/testcases/101'
        )
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 101)
    
    @patch('app.services.azure_devops.AzureDevOpsService._make_request')
    def test_link_work_items(self, mock_make_request):
        """Test linking work items."""
        # Mock response
        mock_make_request.return_value = {'id': 123, 'relations': [{'rel': 'Microsoft.VSTS.Common.TestedBy-Forward'}]}
        
        # Link work items
        result = self.service.link_work_items(123, 101)
        
        # Check that the request was made correctly
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        
        self.assertEqual(args[0], 'PATCH')
        self.assertEqual(args[1], 'https://dev.azure.com/test-org/test-project/_apis/wit/workitems/123')
        
        # Check operations in the request JSON
        operations = kwargs['json_data']
        self.assertEqual(len(operations), 1)
        
        # Check that the relation is set correctly
        self.assertEqual(operations[0]['op'], 'add')
        self.assertEqual(operations[0]['path'], '/relations/-')
        self.assertEqual(operations[0]['value']['rel'], 'Microsoft.VSTS.Common.TestedBy-Forward')
        self.assertEqual(operations[0]['value']['url'], 'https://dev.azure.com/test-org/test-project/_apis/wit/workitems/101')
        
        # Check that the response was returned correctly
        self.assertEqual(result['id'], 123)
    
    @patch('app.services.azure_devops.AzureDevOpsService.get_work_item')
    @patch('app.services.azure_devops.AzureDevOpsService.create_test_plan')
    @patch('app.services.azure_devops.AzureDevOpsService.create_test_suite')
    @patch('app.services.azure_devops.AzureDevOpsService.create_test_case')
    @patch('app.services.azure_devops.AzureDevOpsService.add_test_case_to_suite')
    @patch('app.services.azure_devops.AzureDevOpsService.link_work_items')
    def test_create_test_cases_for_story(self, mock_link, mock_add, mock_create_tc, mock_create_suite, mock_create_plan, mock_get):
        """Test creating test cases for a user story."""
        # Mock responses
        mock_get.return_value = {'id': 123, 'fields': {'System.Title': 'User Story Title'}}
        mock_create_plan.return_value = {'id': 456, 'name': 'Test Plan for User Story Title'}
        mock_create_suite.return_value = {'id': 789, 'name': 'Test Suite for User Story Title'}
        mock_create_tc.side_effect = [
            {'id': 101, 'url': 'https://dev.azure.com/test-org/test-project/_apis/wit/workItems/101'},
            {'id': 102, 'url': 'https://dev.azure.com/test-org/test-project/_apis/wit/workItems/102'}
        ]
        mock_add.return_value = {}
        mock_link.return_value = {}
        
        # Create test cases
        test_cases = [
            TestCaseRecord(
                story_id='123',
                title='Test Case 1',
                description='Test case 1 description',
                steps=[{'action': 'Step 1', 'expected': 'Expected Result 1'}],
                test_case_text='# Test Case 1\n\nTest case 1 description'
            ),
            TestCaseRecord(
                story_id='123',
                title='Test Case 2',
                description='Test case 2 description',
                steps=[{'action': 'Step 2', 'expected': 'Expected Result 2'}],
                test_case_text='# Test Case 2\n\nTest case 2 description'
            )
        ]
        
        result = self.service.create_test_cases_for_story(123, test_cases)
        
        # Check that all the methods were called correctly
        mock_get.assert_called_once_with(123)
        mock_create_plan.assert_called_once_with('Test Plan for User Story Title', 'Test plan for user story: User Story Title')
        mock_create_suite.assert_called_once_with(456, 'Test Suite for User Story Title')
        
        # Check that create_test_case was called twice (once for each test case)
        self.assertEqual(mock_create_tc.call_count, 2)
        mock_create_tc.assert_any_call(test_cases[0])
        mock_create_tc.assert_any_call(test_cases[1])
        
        # Check that add_test_case_to_suite was called twice
        self.assertEqual(mock_add.call_count, 2)
        mock_add.assert_any_call(456, 789, 101)
        mock_add.assert_any_call(456, 789, 102)
        
        # Check that link_work_items was called twice
        self.assertEqual(mock_link.call_count, 2)
        mock_link.assert_any_call(123, 101)
        mock_link.assert_any_call(123, 102)
        
        # Check that the test case IDs were updated
        self.assertEqual(test_cases[0].test_case_id, '101')
        self.assertEqual(test_cases[1].test_case_id, '102')
        
        # Check that the result contains both test cases
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 101)
        self.assertEqual(result[1]['id'], 102)

if __name__ == '__main__':
    unittest.main()
