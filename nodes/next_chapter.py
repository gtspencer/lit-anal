"""NextChapter node: conditional routing to next chapter or finalization."""

from schemas.state import BookState
from utils.logging_config import get_logger

logger = get_logger()


def next_chapter_node(state: BookState) -> BookState:
    """Update state and determine routing for next chunk, chapter, or finalization.
    
    Checks if more scenes remain in current chapter, or if we should move
    to the next chapter or finalize.
    
    Reads:
    - `chapter_idx`: current chapter index
    - `chapters`: list of chapters
    - `current_scenes`: all scenes in current chapter
    - `processed_scene_ids`: scene IDs already processed
    
    Writes:
    - Updates `chapter_idx` if moving to next chapter
    
    Returns:
        Updated state
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    all_scenes = state.get('current_scenes', [])
    processed_ids = state.get('processed_scene_ids', set())
    
    # Check if more scenes remain in current chapter
    all_scene_ids = {s['scene_id'] for s in all_scenes}
    remaining_scenes = all_scene_ids - processed_ids
    
    if remaining_scenes:
        # More scenes to process in current chapter
        logger.info(f"Chapter {chapter_idx + 1}/{len(chapters)}: {len(remaining_scenes)} scenes remaining, processing next chunk")
        return state
    elif chapter_idx + 1 < len(chapters):
        # Current chapter done, move to next chapter
        updated_state: BookState = {
            **state,
            'chapter_idx': chapter_idx + 1,
        }
        logger.info(f"Chapter {chapter_idx + 1}/{len(chapters)} complete, continuing to next chapter")
        return updated_state
    else:
        # All chapters processed
        logger.info(f"All {len(chapters)} chapters processed, proceeding to finalization")
        return state


def should_continue(state: BookState) -> str:
    """Determine routing decision based on state.
    
    Checks if more scenes remain in current chapter, if more chapters remain,
    or if we should finalize.
    
    Args:
        state: Current state
    
    Returns:
        "next_chunk" if more scenes in current chapter,
        "next_chapter" if more chapters remain,
        "finalize" if all chapters processed
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    all_scenes = state.get('current_scenes', [])
    processed_ids = state.get('processed_scene_ids', set())
    
    # Check if more scenes remain in current chapter
    all_scene_ids = {s['scene_id'] for s in all_scenes}
    remaining_scenes = all_scene_ids - processed_ids
    
    if remaining_scenes:
        return "next_chunk"
    elif chapter_idx + 1 < len(chapters):
        return "next_chapter"
    else:
        return "finalize"

