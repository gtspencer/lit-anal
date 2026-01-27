"""Ranker node: assigns subjective influence ranks to all characters."""

import os
import hashlib
from schemas.state import BookState, FinalCharacterResult
from utils.json import parse_json_safely
from prompts import get_ranker_prompt, PROMPT_VERSION
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


def ranker_node(state: BookState) -> BookState:
    """Assign subjective influence ranks to all characters.
    
    Reads:
    - `book_plot_summary`: overall plot summary
    - `character_dossiers`: character dossiers
    - `book_mentions`: mention counts (reference only)
    - `book_appearances`: appearance counts (reference only)
    - `characters_by_id`: character profiles
    
    Writes:
    - `final_ranked_characters`: list of ranked character results
    - Updates `ranking_run_metadata` with ranker metadata
    
    Args:
        state: Current state
    
    Returns:
        Updated state with final rankings
    """
    book_plot_summary = state.get('book_plot_summary', '')
    character_dossiers = state.get('character_dossiers', {})
    book_mentions = state.get('book_mentions', {})
    book_appearances = state.get('book_appearances', {})
    characters_by_id = state.get('characters_by_id', {})
    
    # Build prompt
    prompt = get_ranker_prompt(
        book_plot_summary,
        character_dossiers,
        book_mentions,
        book_appearances
    )
    
    # Get model configuration from environment
    model = os.getenv("RANKER_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("RANKER_TEMPERATURE", "0.1"))  # Low temperature for more stable rankings
    
    # Call LLM
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    
    final_ranked_characters = []
    
    if parsed and isinstance(parsed, list):
        for rank_data in parsed:
            char_id = rank_data.get('character_id', '')
            char = characters_by_id.get(char_id, {})
            
            result: FinalCharacterResult = {
                'rank': int(rank_data.get('rank', 0)),
                'character_id': char_id,
                'name': rank_data.get('name', char.get('canonical_name', 'Unknown')),
                'aliases': rank_data.get('aliases', char.get('aliases', [])),
                'appeared_scenes': int(rank_data.get('appeared_scenes', book_appearances.get(char_id, 0))),
                'mentioned_count': int(rank_data.get('mentioned_count', book_mentions.get(char_id, 0))),
                'influence_summary': rank_data.get('influence_summary', ''),
            }
            
            if 'ranking_rationale' in rank_data:
                result['ranking_rationale'] = rank_data.get('ranking_rationale')
            
            final_ranked_characters.append(result)
    
    # Sort by rank to ensure correct ordering
    final_ranked_characters.sort(key=lambda x: x['rank'])
    
    # Update metadata
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    ranking_run_metadata = state.get('ranking_run_metadata', {})
    ranking_run_metadata.update({
        'ranker_prompt_hash': prompt_hash,
        'ranker_model': model,
        'ranker_temperature': temperature,
    })
    
    updated_state: BookState = {
        **state,
        'final_ranked_characters': final_ranked_characters,
        'ranking_run_metadata': ranking_run_metadata,
    }
    
    return updated_state

