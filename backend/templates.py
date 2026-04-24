# VoiceNote UK - Templates System
# Predefined templates for different note types

from typing import List, Dict, Any
import json

# System templates (available to all users)
SYSTEM_TEMPLATES = [
    {
        "id": "meeting",
        "name": "Meeting Notes",
        "template_type": "meeting",
        "is_global": True,
        "prompt_template": """Analyse this meeting transcript and extract:
- Meeting purpose and objectives
- Key decisions made
- Action items with assignees
- Follow-up meetings or deadlines
- Important quotes or commitments

Structure the notes for easy reference and action tracking.""",
        "sections": {
            "summary": "Meeting overview and main outcomes",
            "key_points": "Important decisions and discussions",
            "action_items": "Tasks with owners and deadlines",
            "attendees": "People mentioned or key participants",
            "next_steps": "Follow-up actions and timelines"
        }
    },
    {
        "id": "lecture",
        "name": "Lecture Notes",
        "template_type": "lecture",
        "is_global": True,
        "prompt_template": """Analyse this lecture transcript and extract:
- Main topic and learning objectives
- Key concepts and definitions
- Important examples or case studies
- Questions or discussion points
- Key takeaways and applications

Structure the notes for effective studying and review.""",
        "sections": {
            "summary": "Lecture overview and main topic",
            "key_points": "Core concepts and definitions",
            "examples": "Important examples and illustrations",
            "questions": "Key questions or discussion points",
            "takeaways": "Main learning outcomes"
        }
    },
    {
        "id": "interview",
        "name": "Interview Notes",
        "template_type": "interview",
        "is_global": True,
        "prompt_template": """Analyse this interview transcript and extract:
- Interviewee background and expertise
- Key insights and perspectives
- Important quotes and statements
- Common themes or patterns
- Follow-up questions or topics

Structure the notes to capture the conversation flow and key insights.""",
        "sections": {
            "summary": "Interview overview and main themes",
            "key_points": "Important insights and perspectives",
            "quotes": "Notable quotes and statements",
            "background": "Interviewee context and expertise",
            "follow_up": "Additional questions or topics to explore"
        }
    },
    {
        "id": "brainstorm",
        "name": "Brainstorm Session",
        "template_type": "brainstorm",
        "is_global": True,
        "prompt_template": """Analyse this brainstorming transcript and extract:
- Problem statement or challenge
- Ideas and suggestions generated
- Pros and cons of different approaches
- Creative solutions proposed
- Next steps or implementation ideas

Structure the notes to capture the creative process and potential solutions.""",
        "sections": {
            "summary": "Session overview and main challenge",
            "key_points": "Ideas and suggestions discussed",
            "solutions": "Proposed solutions and approaches",
            "pros_cons": "Advantages and disadvantages mentioned",
            "next_steps": "Implementation ideas and action items"
        }
    }
]

def get_system_templates() -> List[Dict[str, Any]]:
    """Get all system templates."""
    return SYSTEM_TEMPLATES.copy()

def get_template_by_type(template_type: str) -> Dict[str, Any]:
    """Get a system template by type."""
    for template in SYSTEM_TEMPLATES:
        if template["template_type"] == template_type:
            return template.copy()
    return None

def get_template_prompt(template_type: str, custom_prompt: str = None) -> str:
    """Get the AI prompt for a template type."""
    if custom_prompt:
        return custom_prompt

    template = get_template_by_type(template_type)
    if template and template.get("prompt_template"):
        return template["prompt_template"]

    # Default prompt
    return """Analyse the following spoken transcript and return a JSON object with exactly these fields:

- "summary": A 2-3 sentence summary of the main content.
- "key_points": An array of concise bullet-point strings covering the most important points.
- "action_items": An array of task/follow-up strings (empty array [] if none are mentioned).
- "tone": Exactly one of these strings: "formal", "informal", or "emotional".

Respond with the JSON object only — no markdown, no extra explanation."""

def customize_prompt_for_template(base_prompt: str, template_type: str) -> str:
    """Customize the base AI prompt based on template type."""
    template = get_template_by_type(template_type)
    if not template:
        return base_prompt

    # Add template-specific instructions
    template_instructions = template.get("prompt_template", "")
    if template_instructions:
        return f"{template_instructions}\n\n{base_prompt}"

    return base_prompt