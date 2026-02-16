from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import ProposalRequest, ProposalResponse, ProposalEstimation
from app.workflows.proposal import proposal_workflow, ProposalState
from app.services.callback import send_callback
from app.config import get_settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AI Freelance Proposal Generator",
    description="LangGraph-based AI service for generating freelance proposals",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_proposal(request: ProposalRequest):
    """
    Background task to process proposal generation and send callback.
    
    Args:
        request: The proposal generation request
    """
    logger.info(f"Processing proposal {request.proposal_id}")
    
    try:
        # Initialize workflow state
        initial_state: ProposalState = {
            "request": request,
            "brief_analysis": "",
            "scope": [],
            "estimation": ProposalEstimation(duration_days=0, price=0),
            "proposal_html": "",
            "error": None
        }
        
        # Run the workflow
        final_state = proposal_workflow.invoke(initial_state)
        
        # Prepare response
        if final_state.get('error'):
            response = ProposalResponse(
                proposal_id=request.proposal_id,
                status="failed",
                need_clarification=False,
                summary="Failed to generate proposal",
                scope=[],
                estimation=ProposalEstimation(duration_days=0, price=0),
                content="",
                error=final_state['error']
            )
        else:
            response = ProposalResponse(
                proposal_id=request.proposal_id,
                status="completed",
                need_clarification=False,
                summary="Klien membutuhkan pengembangan software/website dengan fitur spesifik.",
                scope=final_state['scope'],
                estimation=final_state['estimation'],
                content=final_state['proposal_html']
            )
        
        # Send callback to Laravel
        await send_callback(response)
        logger.info(f"Proposal {request.proposal_id} processing completed")
        
    except Exception as e:
        logger.error(f"Error processing proposal {request.proposal_id}: {str(e)}")
        # Send error callback
        error_response = ProposalResponse(
            proposal_id=request.proposal_id,
            status="failed",
            need_clarification=False,
            summary="Error during proposal generation",
            scope=[],
            estimation=ProposalEstimation(duration_days=0, price=0),
            content="",
            error=str(e)
        )
        await send_callback(error_response)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "AI Freelance Proposal Generator",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/generate-proposal")
async def generate_proposal(request: ProposalRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to receive proposal generation requests from Laravel.
    
    Args:
        request: The proposal request payload
        background_tasks: FastAPI background tasks
        
    Returns:
        dict: Acknowledgment response
    """
    logger.info(f"Received proposal request {request.proposal_id}")
    
    # Add background task
    background_tasks.add_task(process_proposal, request)
    
    return {
        "status": "accepted",
        "proposal_id": request.proposal_id,
        "message": "Proposal generation started"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-freelance-ai",
        "models_available": ["claude", "openai"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
