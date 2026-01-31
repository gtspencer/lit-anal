"""InfluenceExtractor node: extracts structured influence evidence per character."""

import os
from schemas.state import BookState, InfluenceEvidence
from utils.json import parse_json_safely
from prompts import get_influence_extraction_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.logging_config import get_logger

logger = get_logger()


def influence_extractor_node(state: BookState) -> BookState:
    """Extract structured influence evidence per character for current scene chunk.
    
    Reads:
    - `current_scene_chunk`: current batch of scenes being processed
    - `characters_by_id`: character profiles
    - `current_chapter_id`: current chapter ID
    
    Writes:
    - `chapter_influence_evidence`: dict mapping char_id -> InfluenceEvidence
    
    Args:
        state: Current state
    
    Returns:
        Updated state with influence evidence extracted
    """
    scene_chunk = state.get('current_scene_chunk', [])
    characters = state.get('characters_by_id', {})
    chapter_id = state['current_chapter_id']
    
    logger.info(f"Extracting influence evidence for chapter {chapter_id}")
    logger.debug(f"Analyzing {len(scene_chunk)} scenes in chunk for {len(characters)} characters")
    
    # Build prompt for LLM using scene chunk (all scenes, no truncation)
    prompt = get_influence_extraction_prompt(scene_chunk, characters)
    
    # Get model configuration from environment
    model = os.getenv("INFLUENCE_EXTRACTOR_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("INFLUENCE_EXTRACTOR_TEMPERATURE", "0.2"))
    
    logger.debug(f"Calling LLM (model: {model}, temperature: {temperature})")
    # Call LLM for influence extraction
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    logger.debug("LLM response received")
    
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
            
            # Log evidence summary
            signal_counts = {k: len(v) for k, v in signals.items()}
            total_signals = sum(signal_counts.values())
            char_name = characters.get(char_id, {}).get('canonical_name', 'Unknown') if char_id in characters else 'Unknown'
            logger.debug(f"Character {char_id} ({char_name}): {total_signals} influence signals ({signal_counts})")
    else:
        logger.warning("Failed to parse influence evidence from LLM response")
    
    logger.info(f"Extracted influence evidence for {len(chapter_evidence)} characters")
    
    updated_state: BookState = {
        **state,
        'chapter_influence_evidence': chapter_evidence,
    }
    
    return updated_state

