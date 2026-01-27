"""MentionCounter node: counts total alias hits across the chapter."""

from collections import defaultdict
from schemas.state import BookState
from utils.aliases import find_all_alias_matches


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
    alias_index = state.get('alias_index', {})
    
    # Find all alias matches
    matches_by_char = find_all_alias_matches(chapter_text, alias_index, case_sensitive=False)
    
    # Count matches per character
    chapter_mentions = {char_id: len(matches) for char_id, matches in matches_by_char.items()}
    
    updated_state: BookState = {
        **state,
        'chapter_mentions_by_char': chapter_mentions,
    }
    
    return updated_state

