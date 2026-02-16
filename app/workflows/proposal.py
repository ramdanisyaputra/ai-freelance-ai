from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, List, Dict, Any
from app.services.llm import llm_service
from app.models import ProposalRequest, ProposalEstimation
from app.prompts import (
    get_introduction_prompt,
    get_needs_assessment_prompt,
    get_approach_prompt,
    get_strengths_prompt,
    get_timeline_prompt,
    get_pricing_prompt,
    get_credentials_prompt,
    get_social_proof_prompt,
    get_terms_prompt,
    LANGUAGE_CONFIGS
)
import logging
import re
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ProposalState(TypedDict):
    """State for enhanced proposal generation workflow."""
    request: ProposalRequest
    brief_analysis: str
    sections: Dict[str, str]  # Store each generated section
    scope: List[str]
    estimation: ProposalEstimation
    proposal_html: str
    error: str | None


def save_step(proposal_id: int, step_name: str, data: Any):
    """Save intermediate step to JSON file."""
    try:
        output_dir = Path(f"/tmp/proposals/{proposal_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"{step_name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved step '{step_name}' for proposal {proposal_id}")
    except Exception as e:
        logger.error(f"Failed to save step '{step_name}': {str(e)}")


def analyze_brief(state: ProposalState) -> ProposalState:
    """Step 1: Analyze the client brief and extract key requirements."""
    logger.info(f"Step 1: Analyzing brief for proposal {state['request'].proposal_id}")
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    
    system_prompt = """You are an expert freelance consultant analyzing client briefs.
Extract and summarize the key requirements, features, and constraints from the client's message.
Be concise but comprehensive. Identify the project type, key features, budget hints, and timeline expectations."""
    
    user_context = f"""
Client Brief: {request.brief}

{f"Freelancer Context: {request.user_brief}" if request.user_brief else ""}

Freelancer Profile:
- Tech Stack: {', '.join(request.freelancer_profile.stack)}
- Rate Type: {request.freelancer_profile.rate_type}
- Minimum Price: {request.freelancer_profile.currency} {request.freelancer_profile.min_price}

Analyze this brief and provide a structured summary of requirements in {'English' if lang == 'en' else 'Indonesian'}.
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_context)
    ]
    
    try:
        response = llm.invoke(messages)
        state['brief_analysis'] = response.content
        save_step(request.proposal_id, "01_brief_analysis", {
            "analysis": response.content,
            "language": lang
        })
        logger.info("Brief analysis completed")
    except Exception as e:
        logger.error(f"Error analyzing brief: {str(e)}")
        state['error'] = f"Failed to analyze brief: {str(e)}"
    
    return state


def generate_scope(state: ProposalState) -> ProposalState:
    """Step 2: Generate project scope based on brief analysis."""
    logger.info(f"Step 2: Generating scope for proposal {state['request'].proposal_id}")
    
    if state.get('error'):
        return state
    
    llm = llm_service.get_primary_model()
    lang = state['request'].language
    
    system_prompt = """You are a project scoping expert.
Based on the brief analysis, generate a list of concrete deliverables/scope items.
Return ONLY a JSON array of scope items as strings, nothing else.
Example: ["Landing Page Design & Development", "Admin Dashboard", "API Integration"]"""
    
    user_prompt = f"""Brief Analysis:
{state['brief_analysis']}

Generate 3-7 specific scope items for this project in {'English' if lang == 'en' else 'Indonesian'}."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        content = re.sub(r'```json\n?', '', content)
        content = re.sub(r'```\n?', '', content)
        
        scope = json.loads(content)
        state['scope'] = scope if isinstance(scope, list) else [content]
        save_step(state['request'].proposal_id, "02_scope", {
            "scope": state['scope'],
            "language": lang
        })
        logger.info(f"Generated {len(state['scope'])} scope items")
    except Exception as e:
        logger.error(f"Error generating scope: {str(e)}")
        state['scope'] = ["Web Development", "UI/UX Design", "Deployment"] if lang == "en" else ["Pengembangan Web", "Desain UI/UX", "Deployment"]
        save_step(state['request'].proposal_id, "02_scope", {
            "scope": state['scope'],
            "language": lang,
            "fallback": True
        })
    
    return state


def estimate_project(state: ProposalState) -> ProposalState:
    """Step 3: Estimate project duration and price."""
    logger.info(f"Step 3: Estimating project for proposal {state['request'].proposal_id}")
    
    if state.get('error'):
        return state
    
    request = state['request']
    scope_count = len(state['scope'])
    
    # Estimation logic
    duration_days = scope_count * 7  # 1 week per scope item
    base_price = request.freelancer_profile.min_price
    price = max(base_price, scope_count * 3500000)  # 3.5M IDR per scope item
    
    state['estimation'] = ProposalEstimation(
        duration_days=duration_days,
        price=price
    )
    
    save_step(request.proposal_id, "03_estimation", {
        "duration_days": duration_days,
        "price": price,
        "currency": request.freelancer_profile.currency,
        "scope_count": scope_count
    })
    
    logger.info(f"Estimated {duration_days} days, {price} {request.freelancer_profile.currency}")
    return state


# Initialize sections dict
def init_sections(state: ProposalState) -> ProposalState:
    """Initialize sections dictionary."""
    state['sections'] = {}
    return state


def generate_introduction(state: ProposalState) -> ProposalState:
    """Step 4: Generate introduction section."""
    logger.info(f"Step 4: Generating introduction")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    
    system_prompt = get_introduction_prompt(lang)
    user_prompt = f"""
Brief Analysis: {state['brief_analysis']}

Freelancer Profile:
- Tech Stack: {', '.join(request.freelancer_profile.stack)}
{f"- Background: {request.user_brief}" if request.user_brief else ""}

Generate a professional introduction."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['introduction'] = content
        save_step(request.proposal_id, "04_introduction", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating introduction: {str(e)}")
        state['sections']['introduction'] = "<p>Hello, I'm a professional web developer ready to help with your project.</p>"
    
    return state


def generate_needs_assessment(state: ProposalState) -> ProposalState:
    """Step 5: Generate needs assessment section."""
    logger.info(f"Step 5: Generating needs assessment")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_needs_assessment_prompt(lang)
    user_prompt = f"""
Client Brief: {request.brief}
Brief Analysis: {state['brief_analysis']}

Generate a needs assessment that shows understanding of the client's goals."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['needs'] = content
        save_step(request.proposal_id, "05_needs_assessment", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating needs assessment: {str(e)}")
        state['sections']['needs'] = f"<h3>{config['needs_title']}</h3><p>I understand your project requirements.</p>"
    
    return state


def generate_approach(state: ProposalState) -> ProposalState:
    """Step 6: Generate proposed approach section."""
    logger.info(f"Step 6: Generating approach")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_approach_prompt(lang)
    user_prompt = f"""
Brief Analysis: {state['brief_analysis']}
Scope: {', '.join(state['scope'])}

Generate a clear, high-level approach for this project."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['approach'] = content
        save_step(request.proposal_id, "06_approach", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating approach: {str(e)}")
        state['sections']['approach'] = f"<h3>{config['approach_title']}</h3><p>I will follow a structured development process.</p>"
    
    return state


def generate_strengths(state: ProposalState) -> ProposalState:
    """Step 7: Generate strengths section."""
    logger.info(f"Step 7: Generating strengths")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_strengths_prompt(lang)
    user_prompt = f"""
Tech Stack: {', '.join(request.freelancer_profile.stack)}
{f"Background: {request.user_brief}" if request.user_brief else ""}

Generate a compelling strengths section."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['strengths'] = content
        save_step(request.proposal_id, "07_strengths", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating strengths: {str(e)}")
        state['sections']['strengths'] = f"<h3>{config['strengths_title']}</h3><ul><li>Technical expertise</li><li>Strong communication</li></ul>"
    
    return state


def generate_timeline(state: ProposalState) -> ProposalState:
    """Step 8: Generate timeline section."""
    logger.info(f"Step 8: Generating timeline")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_timeline_prompt(lang)
    user_prompt = f"""
Estimated Duration: {state['estimation'].duration_days} days
Scope: {', '.join(state['scope'])}

Generate a realistic timeline section."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['timeline'] = content
        save_step(request.proposal_id, "08_timeline", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating timeline: {str(e)}")
        state['sections']['timeline'] = f"<h3>{config['timeline_title']}</h3><p>{state['estimation'].duration_days} days</p>"
    
    return state


def generate_pricing(state: ProposalState) -> ProposalState:
    """Step 9: Generate pricing section."""
    logger.info(f"Step 9: Generating pricing")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_pricing_prompt(lang)
    user_prompt = f"""
Price: {request.freelancer_profile.currency} {state['estimation'].price:,}
Scope: {', '.join(state['scope'])}

Generate a professional pricing section."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['pricing'] = content
        save_step(request.proposal_id, "09_pricing", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating pricing: {str(e)}")
        state['sections']['pricing'] = f"<h3>{config['pricing_title']}</h3><p>{request.freelancer_profile.currency} {state['estimation'].price:,}</p>"
    
    return state


def generate_credentials(state: ProposalState) -> ProposalState:
    """Step 10: Generate credentials section."""
    logger.info(f"Step 10: Generating credentials")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_credentials_prompt(lang)
    user_prompt = f"""
Tech Stack: {', '.join(request.freelancer_profile.stack)}

Generate a credentials section."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['credentials'] = content
        save_step(request.proposal_id, "10_credentials", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating credentials: {str(e)}")
        state['sections']['credentials'] = f"<h3>{config['credentials_title']}</h3><ul><li>Professional tools</li></ul>"
    
    return state


def generate_social_proof(state: ProposalState) -> ProposalState:
    """Step 11: Generate social proof section."""
    logger.info(f"Step 11: Generating social proof")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_social_proof_prompt(lang)
    user_prompt = f"""
{f"Background: {request.user_brief}" if request.user_brief else ""}

Generate a social proof section with example testimonials."""
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['social_proof'] = content
        save_step(request.proposal_id, "11_social_proof", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating social proof: {str(e)}")
        state['sections']['social_proof'] = f"<h3>{config['social_proof_title']}</h3><p>Proven track record.</p>"
    
    return state


def generate_terms(state: ProposalState) -> ProposalState:
    """Step 12: Generate terms section."""
    logger.info(f"Step 12: Generating terms")
    
    if state.get('error'):
        return state
    
    request = state['request']
    llm = llm_service.get_primary_model()
    lang = request.language
    config = LANGUAGE_CONFIGS[lang]
    
    system_prompt = get_terms_prompt(lang)
    user_prompt = "Generate a professional terms and expectations section."
    
    try:
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        content = clean_html(response.content)
        state['sections']['terms'] = content
        save_step(request.proposal_id, "12_terms", {"content": content, "language": lang})
    except Exception as e:
        logger.error(f"Error generating terms: {str(e)}")
        state['sections']['terms'] = f"<h3>{config['terms_title']}</h3><p>Clear communication and delivery.</p>"
    
    return state


def assemble_proposal(state: ProposalState) -> ProposalState:
    """Step 13: Assemble all sections into final HTML proposal."""
    logger.info(f"Step 13: Assembling final proposal")
    
    if state.get('error'):
        return state
    
    sections = state['sections']
    
    # Assemble in professional order
    html_parts = [
        sections.get('introduction', ''),
        sections.get('needs', ''),
        sections.get('approach', ''),
        sections.get('strengths', ''),
        sections.get('timeline', ''),
        sections.get('pricing', ''),
        sections.get('credentials', ''),
        sections.get('social_proof', ''),
        sections.get('terms', ''),
    ]
    
    state['proposal_html'] = '\n\n'.join(filter(None, html_parts))
    
    save_step(state['request'].proposal_id, "13_final_proposal", {
        "html": state['proposal_html'],
        "language": state['request'].language,
        "sections_count": len([s for s in html_parts if s])
    })
    
    logger.info("Final proposal assembled successfully")
    return state


def clean_html(content: str) -> str:
    """Clean HTML content by removing markdown code blocks."""
    content = re.sub(r'```html\n?', '', content)
    content = re.sub(r'```\n?', '', content)
    return content.strip()


# Build the enhanced workflow graph
def create_proposal_workflow() -> StateGraph:
    """Create the enhanced 13-step LangGraph workflow for professional proposal generation."""
    workflow = StateGraph(ProposalState)
    
    # Add all nodes
    workflow.add_node("analyze_brief", analyze_brief)
    workflow.add_node("generate_scope", generate_scope)
    workflow.add_node("estimate_project", estimate_project)
    workflow.add_node("init_sections", init_sections)
    workflow.add_node("generate_introduction", generate_introduction)
    workflow.add_node("generate_needs_assessment", generate_needs_assessment)
    workflow.add_node("generate_approach", generate_approach)
    workflow.add_node("generate_strengths", generate_strengths)
    workflow.add_node("generate_timeline", generate_timeline)
    workflow.add_node("generate_pricing", generate_pricing)
    workflow.add_node("generate_credentials", generate_credentials)
    workflow.add_node("generate_social_proof", generate_social_proof)
    workflow.add_node("generate_terms", generate_terms)
    workflow.add_node("assemble_proposal", assemble_proposal)
    
    # Define edges (sequential flow)
    workflow.set_entry_point("analyze_brief")
    workflow.add_edge("analyze_brief", "generate_scope")
    workflow.add_edge("generate_scope", "estimate_project")
    workflow.add_edge("estimate_project", "init_sections")
    workflow.add_edge("init_sections", "generate_introduction")
    workflow.add_edge("generate_introduction", "generate_needs_assessment")
    workflow.add_edge("generate_needs_assessment", "generate_approach")
    workflow.add_edge("generate_approach", "generate_strengths")
    workflow.add_edge("generate_strengths", "generate_timeline")
    workflow.add_edge("generate_timeline", "generate_pricing")
    workflow.add_edge("generate_pricing", "generate_credentials")
    workflow.add_edge("generate_credentials", "generate_social_proof")
    workflow.add_edge("generate_social_proof", "generate_terms")
    workflow.add_edge("generate_terms", "assemble_proposal")
    workflow.add_edge("assemble_proposal", END)
    
    return workflow.compile()


# Global workflow instance
proposal_workflow = create_proposal_workflow()
