"""Init/ValidateInput node: validates input and initializes state structures."""

from typing import TypedDict
from schemas.state import BookState
from utils.logging_config import get_logger

logger = get_logger()


def init_node(state: BookState) -> BookState:
    """Initialize and validate input state.
    
    Reads:
    - `chapters`: list of chapter inputs
    
    Writes:
    - Initializes all empty structures in state
    - Validates that chapters list is present and properly shaped
    
    Args:
        state: Current state
    
    Returns:
        Updated state with initialized structures
    """
    logger.info("Initializing and validating input state")
    
    # Validate chapters
    if 'chapters' not in state or not state['chapters']:
        logger.error("State must contain a non-empty 'chapters' list")
        raise ValueError("State must contain a non-empty 'chapters' list")
    
    num_chapters = len(state['chapters'])
    logger.debug(f"Validating {num_chapters} chapters")
    
    for i, chapter in enumerate(state['chapters']):
        if 'chapter_id' not in chapter or 'text' not in chapter:
            logger.error(f"Chapter {i} missing required fields")
            raise ValueError(f"Chapter {i} must have 'chapter_id' and 'text' fields")
        if not isinstance(chapter['text'], str) or not chapter['text'].strip():
            logger.error(f"Chapter {i} has empty text field")
            raise ValueError(f"Chapter {i} must have non-empty 'text' field")
    
    logger.info(f"Validated {num_chapters} chapters successfully")
    
    # Initialize state structures
    updated_state: BookState = {
        **state,
        'chapter_idx': state.get('chapter_idx', 0),
        'characters_by_id': state.get('characters_by_id', {}),
        'alias_index': state.get('alias_index', {}),
        'unresolved_aliases': state.get('unresolved_aliases', {}),
        'book_mentions': state.get('book_mentions', {}),
        'book_appearances': state.get('book_appearances', {}),
        'book_influence': state.get('book_influence', {}),
    }
    
    logger.debug("State structures initialized")
    return updated_state

