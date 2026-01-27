"""BookSynthesis node: compresses book-wide evidence into dossiers."""

from schemas.state import BookState, CharacterDossier
from utils.json import parse_json_safely
from prompts import get_book_synthesis_prompt, PROMPT_VERSION
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import hashlib


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
    
    # Build prompt
    prompt = get_book_synthesis_prompt(
        book_influence,
        book_mentions,
        book_appearances,
        characters_by_id
    )
    
    # Call LLM
    model = "gpt-4o-mini"
    temperature = 0.2
    llm = ChatOpenAI(model=model, temperature=temperature)
    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content
    
    # Parse JSON response
    parsed = parse_json_safely(response_text)
    
    book_plot_summary = ""
    character_dossiers = {}
    
    if parsed:
        book_plot_summary = parsed.get('book_plot_summary', '')
        
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

