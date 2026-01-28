"""MentionCounter node: counts total alias hits across the chapter."""

from collections import defaultdict
from schemas.state import BookState
from utils.aliases import find_all_alias_matches
from utils.logging_config import get_logger

logger = get_logger()


def mention_counter_node(state: BookState) -> BookState:
    """Count total alias hits across the chapter for each character.
    
    Reads:
    - `current_chapter_text`: text of current chapter
    - `alias_index`: alias to char_id mapping
    
    Writes:
    - `chapter_mentions_by_char`: dict mapping char_id -> mention count
    
    Args:
        state: Current state
    
    Returns:
        Updated state with mention counts
    """
    chapter_text = state['current_chapter_text']
    chapter_id = state['current_chapter_id']
    alias_index = state.get('alias_index', {})
    
    logger.info(f"Counting mentions in chapter {chapter_id}")
    logger.debug(f"Alias index contains {len(alias_index)} aliases")
    
    # Find all alias matches
    matches_by_char = find_all_alias_matches(chapter_text, alias_index, case_sensitive=False)
    
    # Count matches per character
    chapter_mentions = {char_id: len(matches) for char_id, matches in matches_by_char.items()}
    
    total_mentions = sum(chapter_mentions.values())
    logger.info(f"Found {total_mentions} total mentions across {len(chapter_mentions)} characters")
    if chapter_mentions:
        top_mentioned = max(chapter_mentions.items(), key=lambda x: x[1])
        logger.debug(f"Most mentioned: {top_mentioned[0]} with {top_mentioned[1]} mentions")
    
    updated_state: BookState = {
        **state,
        'chapter_mentions_by_char': chapter_mentions,
    }
    
    return updated_state

