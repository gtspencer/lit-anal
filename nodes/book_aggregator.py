"""BookAggregator node: merges per-chapter results into book-level totals."""

from schemas.state import BookState, InfluenceAccumulator, InfluenceFeatureTotals
from utils.logging_config import get_logger

logger = get_logger()


def book_aggregator_node(state: BookState) -> BookState:
    """Merge per-chapter results into book-level aggregates.
    
    Aggregates mention counts and influence evidence from the current chapter
    into book-level totals. Note: This aggregates per scene chunk, so it may
    be called multiple times per chapter.
    
    Reads:
    - `chapter_mentions_by_char`: per-chapter mention counts (accumulated across chunks)
    - `chapter_influence_evidence`: per-chapter influence evidence (from current chunk)
    
    Writes:
    - Increments `book_mentions` with chapter totals
    - Appends to `book_influence[char_id].evidence`
    - Updates `book_influence[char_id].feature_totals`
    
    Args:
        state: Current state
    
    Returns:
        Updated state with book-level aggregates updated
    """
    chapter_id = state['current_chapter_id']
    chapter_mentions = state.get('chapter_mentions_by_char', {})
    chapter_evidence = state.get('chapter_influence_evidence', {})
    
    logger.info(f"Aggregating chapter {chapter_id} results into book totals")
    
    book_mentions = state.get('book_mentions', {}).copy()
    book_influence = state.get('book_influence', {}).copy()
    
    # Aggregate mentions (chapter totals, accumulated across all chunks)
    mentions_added = 0
    for char_id, count in chapter_mentions.items():
        book_mentions[char_id] = book_mentions.get(char_id, 0) + count
        mentions_added += count
    
    # Aggregate influence evidence (from current chunk)
    evidence_added = 0
    for char_id, evidence in chapter_evidence.items():
        if char_id not in book_influence:
            book_influence[char_id] = {
                'evidence': [],
                'feature_totals': {
                    'causal_events': 0,
                    'social_turns': 0,
                    'world_shifts': 0,
                    'pacing_beats': 0,
                    'centered_scenes': 0,
                },
            }
        
        # Append evidence
        book_influence[char_id]['evidence'].append(evidence)
        evidence_added += 1
        
        # Update feature totals
        signals = evidence.get('signals', {})
        totals = book_influence[char_id].get('feature_totals', {})
        totals['causal_events'] = totals.get('causal_events', 0) + len(signals.get('causal', []))
        totals['social_turns'] = totals.get('social_turns', 0) + len(signals.get('social', []))
        totals['world_shifts'] = totals.get('world_shifts', 0) + len(signals.get('world', []))
        totals['pacing_beats'] = totals.get('pacing_beats', 0) + len(signals.get('pacing', []))
        totals['centered_scenes'] = totals.get('centered_scenes', 0) + len(signals.get('narrative_gravity', []))
        book_influence[char_id]['feature_totals'] = totals
    
    logger.info(f"Aggregated: {mentions_added} mentions, {evidence_added} evidence entries")
    logger.debug(f"Book totals: {len(book_mentions)} characters with mentions, {len(book_influence)} with influence evidence")
    
    updated_state: BookState = {
        **state,
        'book_mentions': book_mentions,
        'book_influence': book_influence,
    }
    
    return updated_state

