"""Main entry point for the book character influence analyzer.

CLI usage:
    python main.py --input chapters.json --output results.json
    python main.py --input-dir chapters/ --output results.json
    python main.py --input-file book.txt --output results.json
"""

import argparse
import uuid
from pathlib import Path
from dotenv import load_dotenv
from graph import get_app
from book_io.load_chapters import (
    load_chapters_from_json,
    load_chapters_from_directory,
    load_chapters_from_single_file,
)
from book_io.write_results import write_results_json, write_full_state_json
from observability.langsmith import invoke_with_tracing, build_run_metadata, build_tags
from schemas.state import BookState
from utils.logging_config import setup_logging, get_logger

# Load environment variables from .env file
load_dotenv()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze book chapters and rank characters by influence"
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        type=str,
        help="Path to JSON file with chapters array"
    )
    input_group.add_argument(
        "--input-dir",
        type=str,
        help="Directory containing chapter text files"
    )
    input_group.add_argument(
        "--input-file",
        type=str,
        help="Single text file with chapters separated by ---"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--full-state",
        type=str,
        help="Optional: path to write full state JSON (for debugging)"
    )
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include ranking metadata in output JSON"
    )
    
    # Run metadata
    parser.add_argument(
        "--book-id",
        type=str,
        help="Book identifier for tracing"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Run identifier (defaults to UUID)"
    )
    parser.add_argument(
        "--env",
        type=str,
        default="dev",
        help="Environment (dev/prod)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Optional: path to log file (logs also go to console)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(log_file=args.log_file, log_level=args.log_level)
    
    # Load chapters
    logger.info("Loading chapters...")
    if args.input:
        logger.debug(f"Loading from JSON file: {args.input}")
        chapters = load_chapters_from_json(args.input)
    elif args.input_dir:
        logger.debug(f"Loading from directory: {args.input_dir}")
        chapters = load_chapters_from_directory(args.input_dir)
    elif args.input_file:
        logger.debug(f"Loading from single file: {args.input_file}")
        chapters = load_chapters_from_single_file(args.input_file)
    else:
        raise ValueError("Must provide --input, --input-dir, or --input-file")
    
    logger.info(f"Loaded {len(chapters)} chapters")
    
    # Initialize state
    initial_state: BookState = {
        'chapters': chapters,
        'chapter_idx': 0,
        'characters_by_id': {},
        'alias_index': {},
        'unresolved_aliases': {},
        'book_mentions': {},
        'book_influence': {},
        'chapter_summaries': {},
    }
    
    # Get graph app
    app = get_app()
    
    # Build run metadata and tags
    run_id = args.run_id or str(uuid.uuid4())
    book_id = args.book_id or Path(args.output).stem
    
    run_meta = build_run_metadata(
        book_id=book_id,
        run_id=run_id,
        env=args.env,
    )
    
    tags = build_tags(
        book_id=book_id,
        run_id=run_id,
        stage=args.env,
    )
    
    # Execute graph
    logger.info("Executing graph...")
    logger.debug(f"Run ID: {run_id}, Book ID: {book_id}")
    final_state = invoke_with_tracing(
        app,
        initial_state,
        run_meta=run_meta,
        tags=tags,
        thread_id=run_id,  # Use run_id as thread_id for grouping in LangSmith
    )
    
    logger.info("Graph execution complete")
    
    # Write results
    logger.info(f"Writing results to {args.output}...")
    write_results_json(
        final_state,
        args.output,
        include_metadata=args.include_metadata,
    )
    
    if args.full_state:
        logger.info(f"Writing full state to {args.full_state}...")
        write_full_state_json(final_state, args.full_state)
    
    # Print summary
    ranked = final_state.get('final_ranked_characters', [])
    logger.info(f"Ranked {len(ranked)} characters")
    logger.info("Top 5 characters by influence:")
    for char in ranked[:5]:
        logger.info(f"  {char['rank']}. {char['name']} (ID: {char['character_id']})")
        logger.info(f"     Mentioned {char['mentioned_count']} times")


if __name__ == "__main__":
    main()

