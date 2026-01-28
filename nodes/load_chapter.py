"""LoadChapter node: loads current chapter and resets per-chapter scratch fields."""

from schemas.state import BookState
from utils.logging_config import get_logger

logger = get_logger()


def load_chapter_node(state: BookState) -> BookState:
    """Load the current chapter and reset per-chapter scratch fields.
    
    Reads:
    - `chapters`: list of chapter inputs
    - `chapter_idx`: current chapter index
    
    Writes:
    - `current_chapter_id`: ID of current chapter
    - `current_chapter_text`: text of current chapter
    - Resets all per-chapter scratch fields
    
    Args:
        state: Current state
    
    Returns:
        Updated state with current chapter loaded
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    
    if chapter_idx >= len(chapters):
        logger.error(f"Chapter index {chapter_idx} out of range (max: {len(chapters) - 1})")
        raise ValueError(f"Chapter index {chapter_idx} out of range (max: {len(chapters) - 1})")
    
    current_chapter = chapters[chapter_idx]
    chapter_id = current_chapter['chapter_id']
    chapter_text_length = len(current_chapter['text'])
    
    logger.info(f"Loading chapter {chapter_idx + 1}/{len(chapters)}: {chapter_id} ({chapter_text_length} chars)")
    
    # Update state with current chapter
    updated_state: BookState = {
        **state,
        'current_chapter_id': chapter_id,
        'current_chapter_text': current_chapter['text'],
        # Reset per-chapter scratch fields
        'current_scenes': [],
        'chapter_mentions_by_char': {},
        'chapter_appearances_by_char': {},
        'chapter_influence_evidence': {},
    }
    
    logger.debug("Per-chapter scratch fields reset")
    return updated_state

