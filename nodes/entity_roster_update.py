"""EntityRosterUpdate node: maintains character canon and alias registry."""

import os
import json
from typing import Any
from schemas.state import BookState, CharacterProfile, UnresolvedAliasOccurrence
from utils.aliases import build_alias_index
from utils.json import parse_json_safely
from prompts import get_entity_roster_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.logging_config import get_logger

logger = get_logger()


def entity_roster_update_node(state: BookState) -> BookState:
    """Update character roster and alias index for current scene chunk.
    
    Reads:
    - `current_scene_chunk`: current batch of scenes being processed
    - `characters_by_id`: existing character profiles
    - `alias_index`: existing alias index
    
    Writes:
    - Updates `characters_by_id` with new characters
    - Updates `alias_index` with new aliases
    - Adds ambiguous references to `unresolved_aliases`
    
    Args:
        state: Current state
    
    Returns:
        Updated state with character roster updated
    """
    chapter_id = state['current_chapter_id']
    scene_chunk = state.get('current_scene_chunk', [])
    existing_characters = state.get('characters_by_id', {})
    existing_alias_index = state.get('alias_index', {})
    
    num_existing = len(existing_characters)
    
    logger.info(f"Updating entity roster for chapter {chapter_id}")
    logger.debug(f"Existing characters: {num_existing}, Scene chunk: {len(scene_chunk)} scenes")
    
    # Build prompt for LLM using scene chunk
    prompt = get_entity_roster_prompt(existing_characters, scene_chunk)
    
    # Get model configuration from environment
    model = os.getenv("ENTITY_ROSTER_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("ENTITY_ROSTER_TEMPERATURE", "0.1"))
    
    logger.debug(f"Calling LLM (model: {model}, temperature: {temperature})")
    # Call LLM for character detection
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    logger.debug("LLM response received")
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    updated_characters = existing_characters.copy()
    updated_unresolved = state.get('unresolved_aliases', {}).copy()
    
    if not parsed:
        logger.warning("Failed to parse LLM response, continuing with existing characters")
        # Fallback: continue with existing characters
        updated_alias_index = existing_alias_index.copy()
    else:
        # Process new characters
        new_chars = parsed.get('new_characters', [])
        logger.info(f"Detected {len(new_chars)} new characters")
        
        next_char_id = max(
            [int(cid.split('_')[1]) for cid in updated_characters.keys() if cid.startswith('char_')],
            default=0
        ) + 1
        
        for new_char in new_chars:
            char_id = f"char_{next_char_id:03d}"
            next_char_id += 1
            char_name = new_char.get('canonical_name', 'Unknown')
            
            updated_characters[char_id] = {
                'id': char_id,
                'canonical_name': char_name,
                'aliases': new_char.get('aliases', []),
                'notes': new_char.get('notes', []),
            }
            logger.debug(f"Added new character: {char_name} (ID: {char_id})")
        
        # Process alias updates
        alias_updates = parsed.get('alias_updates', [])
        if alias_updates:
            logger.info(f"Processing {len(alias_updates)} alias updates")
        for update in alias_updates:
            char_id = update.get('character_id')
            if char_id in updated_characters:
                existing_aliases = set(updated_characters[char_id].get('aliases', []))
                new_aliases = set(update.get('new_aliases', []))
                updated_characters[char_id]['aliases'] = list(existing_aliases | new_aliases)
                logger.debug(f"Updated aliases for {char_id}: {list(new_aliases)}")
        
        # Process ambiguous references
        ambiguous = parsed.get('ambiguous_references', [])
        if ambiguous:
            logger.warning(f"Found {len(ambiguous)} ambiguous references")
        for ambig in ambiguous:
            occurrence: UnresolvedAliasOccurrence = {
                'chapter_id': chapter_id,
                'scene_id': None,  # Could be enhanced to track scene
                'alias': ambig.get('alias', ''),
                'context': ambig.get('context', ''),
                'candidates': ambig.get('candidates', []),
                'reason': ambig.get('reason', 'Unknown'),
            }
            
            alias_key = ambig.get('alias', '').lower()
            if alias_key not in updated_unresolved:
                updated_unresolved[alias_key] = []
            updated_unresolved[alias_key].append(occurrence)
        
        # Rebuild alias index
        updated_alias_index = build_alias_index(updated_characters)
        logger.debug(f"Rebuilt alias index with {len(updated_alias_index)} aliases")
    
    logger.info(f"Entity roster updated: {len(updated_characters)} total characters")
    
    updated_state: BookState = {
        **state,
        'characters_by_id': updated_characters,
        'alias_index': updated_alias_index,
        'unresolved_aliases': updated_unresolved,
    }
    
    return updated_state

