"""ChapterSummarizer node: incrementally summarizes chapters as scenes are processed."""

import os
from schemas.state import BookState
from utils.json import parse_json_safely
from prompts import get_chapter_summary_prompt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.logging_config import get_logger

logger = get_logger()


def chapter_summarizer_node(state: BookState) -> BookState:
    """Generate or update chapter summary based on current scene chunk.
    
    This node incrementally builds chapter summaries as scenes are processed.
    Each chunk adds to the previous summary, maintaining narrative flow awareness.
    
    Reads:
    - `current_chapter_id`: current chapter ID
    - `current_scene_chunk`: current batch of scenes being processed
    - `chapter_summaries`: existing chapter summaries
    
    Writes:
    - `chapter_summaries`: updated with new/updated summary for current chapter
    
    Args:
        state: Current state
    
    Returns:
        Updated state with chapter summary updated
    """
    chapter_id = state['current_chapter_id']
    scene_chunk = state.get('current_scene_chunk', [])
    chapter_summaries = state.get('chapter_summaries', {})
    
    previous_summary = chapter_summaries.get(chapter_id, "")
    
    logger.info(f"Summarizing chapter {chapter_id}")
    logger.debug(f"Scene chunk: {len(scene_chunk)} scenes, Previous summary: {len(previous_summary)} chars")
    
    # Build prompt for LLM
    prompt = get_chapter_summary_prompt(previous_summary, scene_chunk)
    
    # Get model configuration from environment
    model = os.getenv("CHAPTER_SUMMARIZER_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("CHAPTER_SUMMARIZER_TEMPERATURE", "0.3"))
    
    logger.debug(f"Calling LLM (model: {model}, temperature: {temperature})")
    # Call LLM for summary generation
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    logger.debug("LLM response received")
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    
    updated_summaries = chapter_summaries.copy()
    
    if parsed and 'chapter_summary' in parsed:
        new_summary = parsed['chapter_summary']
        updated_summaries[chapter_id] = new_summary
        logger.info(f"Updated chapter summary ({len(new_summary)} chars)")
    else:
        logger.warning("Failed to parse chapter summary from LLM response")
        # Keep previous summary if parsing fails
        if previous_summary:
            updated_summaries[chapter_id] = previous_summary
    
    updated_state: BookState = {
        **state,
        'chapter_summaries': updated_summaries,
    }
    
    return updated_state

