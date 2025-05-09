"""
Webhook receiver for Azure DevOps service hooks.
Processes user story creation and update events.
"""
import logging
import hmac
import hashlib
import json
from fastapi import APIRouter, Request, Depends, HTTPException, Header, Response, status
from typing import Dict, Any, Optional

from app.config import WEBHOOK_SECRET
from app.models.data_models import UserStoryWebhook, WebhookResponse
from app.services.langgraph_runner import process_user_story

# Configure logging
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

async def verify_webhook_signature(request: Request, x_ado_signature: Optional[str] = Header(None)) -> bool:
    """
    Verify the Azure DevOps webhook signature.
    
    Args:
        request: The incoming request
        x_ado_signature: The signature provided in the header
        
    Returns:
        bool: True if signature is valid, raises exception otherwise
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET not configured. Skipping signature verification.")
        return True
        
    if not x_ado_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature missing"
        )
    
    # Get the raw request body
    body = await request.body()
    
    # Compute the HMAC (SHA256) signature
    computed_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare the signatures
    if not hmac.compare_digest(computed_signature, x_ado_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    return True

def sanitize_user_story(payload: Dict[Any, Any]) -> UserStoryWebhook:
    """
    Extract and sanitize user story details from the webhook payload.
    
    Args:
        payload: The raw webhook payload
        
    Returns:
        UserStoryWebhook: Sanitized user story data
    """
    try:
        # Extract work item data from the payload
        resource = payload.get("resource", {})
        fields = resource.get("fields", {})
        
        # Extract the basic information
        story = UserStoryWebhook(
            story_id=str(resource.get("id", "")),
            project_id=resource.get("projectId", ""),
            title=fields.get("System.Title", "").strip(),
            description=fields.get("System.Description", "").strip(),
            event_type=payload.get("eventType", ""),
            created_by=fields.get("System.CreatedBy", {}).get("displayName", ""),
            work_item_type=resource.get("workItemType", ""),
        )
        
        # Validate that we have the minimum required fields
        if not story.story_id or not story.title:
            raise ValueError("Missing required fields in the payload")
            
        # Additional validation
        if not story.work_item_type.lower() in ["user story", "userstory", "pbi", "product backlog item"]:
            logger.warning(f"Received work item of type {story.work_item_type}, expected 'User Story'")
            
        return story
            
    except Exception as e:
        logger.error(f"Error sanitizing user story: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload structure: {str(e)}"
        )

@router.post("/azure-devops", response_model=WebhookResponse)
async def receive_azure_devops_webhook(
    request: Request,
    _: bool = Depends(verify_webhook_signature)
) -> WebhookResponse:
    """
    Receive webhook notifications from Azure DevOps.
    
    Args:
        request: The incoming request
        _: Dependency to verify webhook signature
        
    Returns:
        WebhookResponse: Status and details of the processed webhook
    """
    try:
        # Parse the request body
        payload = await request.json()
        logger.info(f"Received webhook with event type: {payload.get('eventType', 'unknown')}")
        
        # Only process work item creation and updates
        allowed_events = ["workitem.created", "workitem.updated"]
        event_type = payload.get("eventType", "")
        
        if event_type not in allowed_events:
            logger.info(f"Ignoring event of type: {event_type}")
            return WebhookResponse(
                status="ignored",
                message=f"Event type {event_type} is not processed by this endpoint"
            )
        
        # Extract and sanitize the user story
        user_story = sanitize_user_story(payload)
        
        # Process the user story (this will be implemented in langgraph_runner)
        # For now, we'll just log and acknowledge receipt
        logger.info(f"Processing user story {user_story.story_id}: {user_story.title}")
        
        # Process the user story with LangGraph agent
        result = await process_user_story(user_story)
        return WebhookResponse(
            status="processed",
            message=f"Successfully processed user story {user_story.story_id}",
            details={"story_id": user_story.story_id, "test_cases_created": result.get("test_case_count", 0)}
        )
        
        # Mock response if needed
        return WebhookResponse(
            status="received",
            message=f"Received user story {user_story.story_id}: {user_story.title}",
            details={"story_id": user_story.story_id}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

@router.post("/mock", response_model=WebhookResponse)
async def receive_mock_webhook(request: Request) -> WebhookResponse:
    """
    Endpoint for testing with mocked Azure DevOps payloads.
    This is useful for local development and testing.
    
    Args:
        request: The incoming request
        
    Returns:
        WebhookResponse: Status and details of the processed webhook
    """
    try:
        # Parse the request body
        payload = await request.json()
        
        # Process the payload just like a real webhook
        user_story = sanitize_user_story(payload)
        
        logger.info(f"Processing mock user story {user_story.story_id}: {user_story.title}")
        
        # Process the user story with LangGraph agent
        result = await process_user_story(user_story)
        return WebhookResponse(
            status="processed",
            message=f"Successfully processed mock user story {user_story.story_id}",
            details={"story_id": user_story.story_id, "test_cases_created": result.get("test_case_count", 0)}
        )
        
        # Mock response if needed
        return WebhookResponse(
            status="received",
            message=f"Received mock user story {user_story.story_id}: {user_story.title}",
            details={"story_id": user_story.story_id}
        )
        
    except Exception as e:
        logger.error(f"Error processing mock webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process mock webhook: {str(e)}"
        )
