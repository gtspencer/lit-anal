"""InfluenceExtractor node: extracts structured influence evidence per character."""

import os
from schemas.state import BookState, InfluenceEvidence
from utils.json import parse_json_safely
from prompts import get_influence_extraction_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


def influence_extractor_node(state: BookState) -> BookState:
    """Extract structured influence evidence per character for current chapter.
    
    Reads:
    - `current_scenes`: list of scenes
    - `characters_by_id`: character profiles
    - `current_chapter_id`: current chapter ID
    
    Writes:
    - `chapter_influence_evidence`: dict mapping char_id -> InfluenceEvidence
    
    Args:
        state: Current state
    
    Returns:
        Updated state with influence evidence extracted
    """
    scenes = state['current_scenes']
    characters = state.get('characters_by_id', {})
    chapter_id = state['current_chapter_id']
    
    # Build prompt for LLM
    prompt = get_influence_extraction_prompt(scenes, characters)
    
    # Get model configuration from environment
    model = os.getenv("INFLUENCE_EXTRACTOR_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("INFLUENCE_EXTRACTOR_TEMPERATURE", "0.2"))
    
    # Call LLM for influence extraction
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    
    chapter_evidence = {}
    
    if parsed and 'character_evidence' in parsed:
        for char_id, evidence_data in parsed['character_evidence'].items():
            signals = evidence_data.get('signals', {})
            
            evidence: InfluenceEvidence = {
                'chapter_id': chapter_id,
                'signals': {
                    'causal': signals.get('causal', []),
                    'social': signals.get('social', []),
                    'world': signals.get('world', []),
                    'pacing': signals.get('pacing', []),
                    'narrative_gravity': signals.get('narrative_gravity', []),
                },
            }
            
            if 'salience_score' in evidence_data:
                evidence['salience_score'] = float(evidence_data['salience_score'])
            
            chapter_evidence[char_id] = evidence
    
    updated_state: BookState = {
        **state,
        'chapter_influence_evidence': chapter_evidence,
    }
    
    return updated_state

