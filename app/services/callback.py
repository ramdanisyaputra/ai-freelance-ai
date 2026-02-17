import httpx
from app.config import get_settings
from app.models import ProposalResponse
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_callback(response: ProposalResponse) -> bool:
    """
    Send proposal generation result back to Laravel backend.
    
    Args:
        response: The proposal response to send
        
    Returns:
        bool: True if callback was successful, False otherwise
    """
    callback_url = f"{settings.laravel_api_url}/api/ai/callback/proposal/{response.proposal_id}"
    
    headers = {
        "Authorization": f"Bearer {settings.laravel_api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            result = await client.post(
                callback_url,
                json=response.model_dump(),
                headers=headers,
                timeout=30.0
            )
            result.raise_for_status()
            logger.info(f"Callback sent successfully for proposal {response.proposal_id}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to send callback for proposal {response.proposal_id}: {str(e)}")
        return False


def send_callback_sync(response: ProposalResponse) -> bool:
    """
    Send proposal generation result back to Laravel backend (Synchronous).
    
    Args:
        response: The proposal response to send
        
    Returns:
        bool: True if callback was successful, False otherwise
    """
    callback_url = f"{settings.laravel_api_url}/api/ai/callback/proposal/{response.proposal_id}"
    
    headers = {
        "Authorization": f"Bearer {settings.laravel_api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client() as client:
            result = client.post(
                callback_url,
                json=response.model_dump(),
                headers=headers,
                timeout=30.0
            )
            result.raise_for_status()
            logger.info(f"Callback sent successfully for proposal {response.proposal_id}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to send callback for proposal {response.proposal_id}: {str(e)}")
        return False
