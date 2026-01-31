"""MentionCounter node: counts total alias hits across the chapter."""

from collections import defaultdict
from schemas.state import BookState
from utils.aliases import find_all_alias_matches
from utils.logging_config import get_logger

logger = get_logger()


def mention_counter_node(state: BookState) -> BookState:
    """Count alias hits across the current scene chunk for each character.
    
    Counts mentions across all scenes in the current chunk. These counts
    will be aggregated at the chapter level in BookAggregator.
    
    Reads:
    - `current_scene_chunk`: current batch of scenes being processed
    - `alias_index`: alias to char_id mapping
    - `chapter_mentions_by_char`: existing mention counts for this chapter
    
    Writes:
    - `chapter_mentions_by_char`: dict mapping char_id -> mention count (accumulated)
    
    Args:
        state: Current state
    
    Returns:
        Updated state with mention counts accumulated
    """
    chapter_id = state['current_chapter_id']
    scene_chunk = state.get('current_scene_chunk', [])
    alias_index = state.get('alias_index', {})
    existing_mentions = state.get('chapter_mentions_by_char', {})
    
    logger.info(f"Counting mentions in scene chunk for chapter {chapter_id}")
    logger.debug(f"Scene chunk: {len(scene_chunk)} scenes, Alias index: {len(alias_index)} aliases")
    
    # Count mentions across all scenes in chunk
    chunk_mentions = {}
    for scene in scene_chunk:
        scene_text = scene['text']
        matches_by_char = find_all_alias_matches(scene_text, alias_index, case_sensitive=False)
        
        # Accumulate counts per character
        for char_id, matches in matches_by_char.items():
            chunk_mentions[char_id] = chunk_mentions.get(char_id, 0) + len(matches)
    
    # Merge with existing chapter mentions
    chapter_mentions = existing_mentions.copy()
    for char_id, count in chunk_mentions.items():
        chapter_mentions[char_id] = chapter_mentions.get(char_id, 0) + count
    
    total_mentions = sum(chunk_mentions.values())
    logger.info(f"Found {total_mentions} mentions in this chunk across {len(chunk_mentions)} characters")
    if chunk_mentions:
        top_mentioned = max(chunk_mentions.items(), key=lambda x: x[1])
        logger.debug(f"Most mentioned in chunk: {top_mentioned[0]} with {top_mentioned[1]} mentions")
    
    updated_state: BookState = {
        **state,
        'chapter_mentions_by_char': chapter_mentions,
    }
    
    return updated_state

