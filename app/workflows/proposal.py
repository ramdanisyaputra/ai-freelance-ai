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
    """Step 3: Estimate project timeline and pricing based on brief analysis."""
    logger.info(f"Step 3: Estimating project for proposal {state['request'].proposal_id}")
    
    if state.get('error'):
        return state
    
    request = state['request']
    scope_count = len(state['scope'])
    llm = llm_service.get_primary_model()
    lang = request.language
    
    # Use AI to estimate based on client budget and freelancer preferences
    system_prompt = """You are an expert freelance project estimator.
Analyze the client's brief and freelancer's profile to provide realistic timeline and pricing estimates.
CRITICAL: Respect the client's stated budget constraints. If they mention a budget, stay within or slightly above it (max 20% over).
Consider the freelancer's preferences for timeline and pricing."""

    user_context = f"""
Client Brief: {request.brief}
Freelancer Timeline Preference: {request.user_brief if request.user_brief else "Standard timeline"}

Scope Items: {', '.join(state['scope'])}
Scope Count: {scope_count}

Freelancer Profile:
- Minimum Price: {request.freelancer_profile.currency} {request.freelancer_profile.min_price}
- Rate Type: {request.freelancer_profile.rate_type}
- Currency: {request.freelancer_profile.currency}

Based on the above, provide:
1. Realistic duration in days (consider freelancer's timeline preference)
2. Fair price in {request.freelancer_profile.currency} (MUST respect client's budget if mentioned)

Respond ONLY with JSON in this exact format:
{{"duration_days": <number>, "price": <number>}}
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_context)
    ]
    
    try:
        response = llm.invoke(messages)
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response.content)
        if json_match:
            estimation_data = json.loads(json_match.group())
            duration_days = int(estimation_data['duration_days'])
            price = int(estimation_data['price'])
        else:
            # Fallback to reasonable defaults
            duration_days = min(scope_count * 5, 30)  # Max 30 days
            price = request.freelancer_profile.min_price
            logger.warning("Could not parse AI estimation, using fallback")
        
        state['estimation'] = ProposalEstimation(
            duration_days=duration_days,
            price=price
        )
        
        save_step(request.proposal_id, "03_estimation", {
            "duration_days": duration_days,
            "price": price,
            "currency": request.freelancer_profile.currency,
            "scope_count": scope_count,
            "ai_response": response.content
        })
        
        logger.info(f"Estimated {duration_days} days, {price} {request.freelancer_profile.currency}")
    except Exception as e:
        logger.error(f"Error estimating project: {str(e)}")
        # Fallback estimation
        duration_days = min(scope_count * 5, 30)
        price = request.freelancer_profile.min_price
        state['estimation'] = ProposalEstimation(
            duration_days=duration_days,
            price=price
        )
        logger.warning(f"Using fallback estimation: {duration_days} days, {price}")
    
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
    """Step 11: Skip social proof section (no fake testimonials)."""
    logger.info(f"Step 11: Skipping social proof section")
    
    if state.get('error'):
        return state
    
    # Skip this section - no fake testimonials
    state['sections']['social_proof'] = ''
    
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
    """Clean HTML content - remove markdown code blocks and non-HTML preamble text."""
    # Remove markdown code fences
    content = re.sub(r'```html\n?', '', content)
    content = re.sub(r'```\n?', '', content)
    content = content.strip()
    
    # Find the first HTML tag and strip any preamble text before it
    first_tag = re.search(r'<(h[1-6]|p|ul|ol|div|section|article|blockquote|table|strong|em|a|span|br)', content, re.IGNORECASE)
    if first_tag:
        preamble = content[:first_tag.start()].strip()
        html_content = content[first_tag.start():]
        
        # If preamble looks like conversational filler, discard it
        # Otherwise, wrap it in a <p> tag if it seems substantial
        conversational_markers = ['here is', 'here\'s', 'sure', 'certainly', 'below is', 'following is', 'output:', 'html:', 'berikut', 'adalah', 'ini']
        is_conversational = any(marker in preamble.lower() for marker in conversational_markers)
        
        if preamble and len(preamble) > 3 and not is_conversational:
            # Only keep preamble if it DOESN'T look like AI chatter
            content = f"<p>{preamble}</p>\n{html_content}"
        else:
            # Discard preamble (it's either empty, too short, or conversational)
            content = html_content
    else:
        # No HTML tags found at all - wrap entire content in paragraphs
        lines = content.split('\n')
        wrapped = []
        for line in lines:
            line = line.strip()
            if line:
                wrapped.append(f"<p>{line}</p>")
        content = '\n'.join(wrapped)
    
    # Clean up any remaining plain text between HTML blocks
    # Split by HTML tags and wrap orphaned text
    content = re.sub(r'(?<=>)\s*\n\s*([^<\n]+)\s*\n\s*(?=<)', lambda m: f'\n<p>{m.group(1).strip()}</p>\n', content)
    
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
