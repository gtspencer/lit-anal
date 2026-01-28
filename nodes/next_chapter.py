"""NextChapter node: conditional routing to next chapter or finalization."""

from schemas.state import BookState
from utils.logging_config import get_logger

logger = get_logger()


def next_chapter_node(state: BookState) -> BookState:
    """Update state and determine routing for next chapter or finalization.
    
    Reads:
    - `chapter_idx`: current chapter index
    - `chapters`: list of chapters
    
    Writes:
    - Updates `chapter_idx` if continuing to next chapter
    
    Returns:
        Updated state
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    
    if chapter_idx + 1 < len(chapters):
        # Update chapter index in state
        updated_state: BookState = {
            **state,
            'chapter_idx': chapter_idx + 1,
        }
        logger.info(f"Chapter {chapter_idx + 1}/{len(chapters)} complete, continuing to next chapter")
        return updated_state
    else:
        logger.info(f"All {len(chapters)} chapters processed, proceeding to finalization")
        return state


def should_continue(state: BookState) -> str:
    """Determine routing decision based on state.
    
    Args:
        state: Current state
    
    Returns:
        "next_chapter" if more chapters remain, "finalize" otherwise
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    
    if chapter_idx + 1 < len(chapters):
        return "next_chapter"
    else:
        return "finalize"

