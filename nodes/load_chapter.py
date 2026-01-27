"""LoadChapter node: loads current chapter and resets per-chapter scratch fields."""

from schemas.state import BookState


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
        raise ValueError(f"Chapter index {chapter_idx} out of range (max: {len(chapters) - 1})")
    
    current_chapter = chapters[chapter_idx]
    
    # Update state with current chapter
    updated_state: BookState = {
        **state,
        'current_chapter_id': current_chapter['chapter_id'],
        'current_chapter_text': current_chapter['text'],
        # Reset per-chapter scratch fields
        'current_scenes': [],
        'chapter_mentions_by_char': {},
        'chapter_appearances_by_char': {},
        'chapter_influence_evidence': {},
    }
    
    return updated_state

