"""BookSynthesis node: compresses book-wide evidence into dossiers."""

import os
import hashlib
from schemas.state import BookState, CharacterDossier
from utils.json import parse_json_safely
from prompts import get_book_synthesis_prompt, PROMPT_VERSION
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from utils.logging_config import get_logger

logger = get_logger()


def book_synthesis_node(state: BookState) -> BookState:
    """Synthesize book-wide evidence into compact dossiers and plot summary.
    
    Reads:
    - `book_influence`: accumulated influence evidence
    - `book_mentions`: total mentions per character
    - `book_appearances`: total appearances per character
    - `characters_by_id`: all character profiles
    
    Writes:
    - `book_plot_summary`: overall plot summary
    - `character_dossiers`: synthesized dossiers per character
    - `ranking_run_metadata`: metadata about this run
    
    Args:
        state: Current state
    
    Returns:
        Updated state with synthesis complete
    """
    book_influence = state.get('book_influence', {})
    book_mentions = state.get('book_mentions', {})
    book_appearances = state.get('book_appearances', {})
    characters_by_id = state.get('characters_by_id', {})
    
    logger.info("Synthesizing book-wide evidence into character dossiers")
    logger.debug(f"Processing {len(characters_by_id)} characters with {len(book_influence)} influence records")
    
    # Build prompt
    prompt = get_book_synthesis_prompt(
        book_influence,
        book_mentions,
        book_appearances,
        characters_by_id
    )
    
    # Get model configuration from environment
    model = os.getenv("BOOK_SYNTHESIS_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("BOOK_SYNTHESIS_TEMPERATURE", "0.2"))
    
    logger.debug(f"Calling LLM (model: {model}, temperature: {temperature})")
    # Call LLM
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    logger.debug("LLM response received")
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    
    book_plot_summary = ""
    character_dossiers = {}
    
    if parsed:
        book_plot_summary = parsed.get('book_plot_summary', '')
        logger.info(f"Generated plot summary ({len(book_plot_summary)} chars)")
        
        for char_id, dossier_data in parsed.get('character_dossiers', {}).items():
            dossier: CharacterDossier = {
                'canonical_name': dossier_data.get('canonical_name', ''),
                'aliases': dossier_data.get('aliases', []),
                'arc_summary': dossier_data.get('arc_summary', ''),
                'relationships': dossier_data.get('relationships', []),
                'impact_summary': dossier_data.get('impact_summary', ''),
                'key_evidence': dossier_data.get('key_evidence', []),
                'uncertainties': dossier_data.get('uncertainties', []),
            }
            character_dossiers[char_id] = dossier
            logger.debug(f"Created dossier for {dossier['canonical_name']} ({len(dossier['key_evidence'])} key evidence points)")
    else:
        logger.error("Failed to parse synthesis response from LLM")
    
    logger.info(f"Synthesis complete: {len(character_dossiers)} dossiers created")
    
    # Store metadata
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    ranking_run_metadata = {
        'prompt_version': PROMPT_VERSION,
        'synthesis_prompt_hash': prompt_hash,
        'synthesis_model': model,
        'synthesis_temperature': temperature,
    }
    
    updated_state: BookState = {
        **state,
        'book_plot_summary': book_plot_summary,
        'character_dossiers': character_dossiers,
        'ranking_run_metadata': ranking_run_metadata,
    }
    
    return updated_state

