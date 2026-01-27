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


def entity_roster_update_node(state: BookState) -> BookState:
    """Update character roster and alias index for current chapter.
    
    Reads:
    - `current_chapter_text`: text of current chapter
    - `current_scenes`: list of scenes
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
    chapter_text = state['current_chapter_text']
    chapter_id = state['current_chapter_id']
    scenes = state['current_scenes']
    existing_characters = state.get('characters_by_id', {})
    existing_alias_index = state.get('alias_index', {})
    
    # Build prompt for LLM
    prompt = get_entity_roster_prompt(chapter_text, existing_characters, scenes)
    
    # Get model configuration from environment
    model = os.getenv("ENTITY_ROSTER_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("ENTITY_ROSTER_TEMPERATURE", "0.1"))
    
    # Call LLM for character detection
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    updated_characters = existing_characters.copy()
    updated_unresolved = state.get('unresolved_aliases', {}).copy()
    
    if not parsed:
        # Fallback: continue with existing characters
        updated_alias_index = existing_alias_index.copy()
    else:
        
        # Process new characters
        next_char_id = max(
            [int(cid.split('_')[1]) for cid in updated_characters.keys() if cid.startswith('char_')],
            default=0
        ) + 1
        
        for new_char in parsed.get('new_characters', []):
            char_id = f"char_{next_char_id:03d}"
            next_char_id += 1
            
            updated_characters[char_id] = {
                'id': char_id,
                'canonical_name': new_char.get('canonical_name', 'Unknown'),
                'aliases': new_char.get('aliases', []),
                'notes': new_char.get('notes', []),
            }
        
        # Process alias updates
        for update in parsed.get('alias_updates', []):
            char_id = update.get('character_id')
            if char_id in updated_characters:
                existing_aliases = set(updated_characters[char_id].get('aliases', []))
                new_aliases = set(update.get('new_aliases', []))
                updated_characters[char_id]['aliases'] = list(existing_aliases | new_aliases)
        
        # Process ambiguous references
        for ambig in parsed.get('ambiguous_references', []):
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
    
    updated_state: BookState = {
        **state,
        'characters_by_id': updated_characters,
        'alias_index': updated_alias_index,
        'unresolved_aliases': updated_unresolved,
    }
    
    return updated_state

