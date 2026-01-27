"""Main entry point for the book character influence analyzer.

CLI usage:
    python main.py --input chapters.json --output results.json
    python main.py --input-dir chapters/ --output results.json
    python main.py --input-file book.txt --output results.json
"""

import argparse
import uuid
from pathlib import Path
from graph import get_app
from io.load_chapters import (
    load_chapters_from_json,
    load_chapters_from_directory,
    load_chapters_from_single_file,
)
from io.write_results import write_results_json, write_full_state_json
from observability.langsmith import invoke_with_tracing, build_run_metadata, build_tags
from schemas.state import BookState


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
    
    args = parser.parse_args()
    
    # Load chapters
    print("Loading chapters...")
    if args.input:
        chapters = load_chapters_from_json(args.input)
    elif args.input_dir:
        chapters = load_chapters_from_directory(args.input_dir)
    elif args.input_file:
        chapters = load_chapters_from_single_file(args.input_file)
    else:
        raise ValueError("Must provide --input, --input-dir, or --input-file")
    
    print(f"Loaded {len(chapters)} chapters")
    
    # Initialize state
    initial_state: BookState = {
        'chapters': chapters,
        'chapter_idx': 0,
        'characters_by_id': {},
        'alias_index': {},
        'unresolved_aliases': {},
        'book_mentions': {},
        'book_appearances': {},
        'book_influence': {},
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
    print("Executing graph...")
    final_state = invoke_with_tracing(
        app,
        initial_state,
        run_meta=run_meta,
        tags=tags,
    )
    
    print("Graph execution complete")
    
    # Write results
    print("Writing results...")
    write_results_json(
        final_state,
        args.output,
        include_metadata=args.include_metadata,
    )
    
    if args.full_state:
        write_full_state_json(final_state, args.full_state)
    
    # Print summary
    ranked = final_state.get('final_ranked_characters', [])
    print(f"\nRanked {len(ranked)} characters")
    print("\nTop 5 characters by influence:")
    for char in ranked[:5]:
        print(f"  {char['rank']}. {char['name']} (ID: {char['character_id']})")
        print(f"     Appeared in {char['appeared_scenes']} scenes, mentioned {char['mentioned_count']} times")


if __name__ == "__main__":
    main()

