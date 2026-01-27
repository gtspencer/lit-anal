"""NextChapter node: conditional routing to next chapter or finalization."""

from schemas.state import BookState


def next_chapter_node(state: BookState) -> str:
    """Determine whether to continue to next chapter or proceed to finalization.
    
    Reads:
    - `chapter_idx`: current chapter index
    - `chapters`: list of chapters
    
    Writes:
    - Updates `chapter_idx` if continuing to next chapter
    
    Returns:
        "next_chapter" if more chapters remain, "finalize" otherwise
    """
    chapter_idx = state['chapter_idx']
    chapters = state['chapters']
    
    if chapter_idx + 1 < len(chapters):
        # Update chapter index in state
        state['chapter_idx'] = chapter_idx + 1
        return "next_chapter"
    else:
        return "finalize"

