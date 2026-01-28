"""Parse book text file into chapter JSON format.

This script extracts chapters from a book text file where:
- Chapter titles are entirely capitalized
- Chapter titles are preceded by at least 2 newlines
- Chapter titles are followed by 1 newline, then the chapter text
"""

import json
import re
import argparse
from pathlib import Path


def normalize_quotes(text: str) -> str:
    """Normalize Unicode curly quotes to standard ASCII quotes.
    
    Converts:
    - " and " → "
    - ' and ' → '
    
    Args:
        text: Text to normalize
    
    Returns:
        Text with normalized quotes
    """
    # Replace curly double quotes with straight quotes
    text = text.replace('\u201c', '"')  # Left double quotation mark
    text = text.replace('\u201d', '"')  # Right double quotation mark
    text = text.replace('\u201e', '"')  # Double low-9 quotation mark
    text = text.replace('\u201f', '"')  # Double high-reversed-9 quotation mark
    
    # Replace curly single quotes with straight quotes
    text = text.replace('\u2018', "'")  # Left single quotation mark
    text = text.replace('\u2019', "'")  # Right single quotation mark
    text = text.replace('\u201a', "'")  # Single low-9 quotation mark
    text = text.replace('\u201b', "'")  # Single high-reversed-9 quotation mark
    
    return text


def is_entirely_uppercase(line: str) -> bool:
    """Check if a line is entirely uppercase (ignoring whitespace and punctuation).
    
    Args:
        line: Line to check
    
    Returns:
        True if line is entirely uppercase, False otherwise
    """
    # Remove whitespace and check if all alphabetic characters are uppercase
    stripped = line.strip()
    if not stripped:
        return False
    
    # Check if all alphabetic characters are uppercase
    alpha_chars = [c for c in stripped if c.isalpha()]
    if not alpha_chars:
        return False
    
    return all(c.isupper() for c in alpha_chars)


def parse_chapters(text: str) -> list[dict]:
    """Parse chapters from book text.
    
    Args:
        text: Full book text
    
    Returns:
        List of chapter dicts with 'chapter_id' and 'text' keys
    """
    chapters = []
    
    # Pattern: at least 1 newline, then a line that's entirely uppercase, then at least 1 newline
    # We'll split on this pattern
    # First, let's find all chapter boundaries
    
    # Split text into lines for easier processing
    lines = text.split('\n')
    
    current_chapter_title = None
    current_chapter_lines = []
    prev_empty_lines = 0
    skipping_after_title = False  # Skip newlines after chapter title
    
    for i, line in enumerate(lines):
        is_empty = not line.strip()
        
        if is_empty:
            prev_empty_lines += 1
            # Skip all newlines immediately after a chapter title (at least 1, but can be more)
            if skipping_after_title:
                # Continue skipping empty lines after title
                continue
            # If we're collecting a chapter, add the empty line
            if current_chapter_title is not None:
                current_chapter_lines.append(line)
        else:
            # Check if this could be a chapter title
            # Need: at least 1 previous empty line AND this line is entirely uppercase
            if prev_empty_lines >= 1 and is_entirely_uppercase(line):
                # Save previous chapter if we have one
                if current_chapter_title is not None:
                    chapter_text = '\n'.join(current_chapter_lines).strip()
                    if chapter_text:
                        chapters.append({
                            'chapter_title': current_chapter_title,
                            'text': chapter_text
                        })
                
                # Start new chapter
                current_chapter_title = normalize_quotes(line.strip())
                current_chapter_lines = []
                prev_empty_lines = 0
                skipping_after_title = True  # Skip all newlines after title (at least 1)
            else:
                # Regular text line
                if current_chapter_title is not None:
                    current_chapter_lines.append(line)
                prev_empty_lines = 0
                skipping_after_title = False  # Stop skipping once we hit non-empty text
    
    # Don't forget the last chapter
    if current_chapter_title is not None:
        chapter_text = '\n'.join(current_chapter_lines).strip()
        if chapter_text:
            # Normalize quotes in chapter text
            chapter_text = normalize_quotes(chapter_text)
            chapters.append({
                'chapter_title': current_chapter_title,
                'text': chapter_text
            })
    
    # If no chapters were found with the pattern, treat entire file as one chapter
    if not chapters:
        print("Warning: No chapters found with expected pattern. Treating entire file as one chapter.")
        chapters.append({
            'chapter_title': 'Chapter 1',
            'text': normalize_quotes(text.strip())
        })
    
    # Convert to expected format with sequential IDs
    result = []
    for i, chapter in enumerate(chapters):
        result.append({
            'chapter_id': f"chapter_{i+1:03d}",
            'text': chapter['text']
        })
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse book text file into chapter JSON format"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input book text file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to output JSON file (default: input_file with .json extension)"
    )
    parser.add_argument(
        "--include-titles",
        action="store_true",
        help="Include chapter titles in output (as metadata)"
    )
    
    args = parser.parse_args()
    
    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file does not exist: {args.input_file}")
        return 1
    
    print(f"Reading book from {args.input_file}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Parsing chapters...")
    chapters = parse_chapters(text)
    
    print(f"Found {len(chapters)} chapters")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.json')
    
    # Prepare output data
    if args.include_titles:
        # Use the already parsed chapters and add titles
        output_data = []
        lines = text.split('\n')
        current_chapter_title = None
        current_chapter_lines = []
        prev_empty_lines = 0
        skipping_after_title = False
        
        for i, line in enumerate(lines):
            is_empty = not line.strip()
            
            if is_empty:
                prev_empty_lines += 1
                if skipping_after_title:
                    # Continue skipping empty lines after title
                    continue
                if current_chapter_title is not None:
                    current_chapter_lines.append(line)
            else:
                if prev_empty_lines >= 1 and is_entirely_uppercase(line):
                    if current_chapter_title is not None:
                        chapter_text = '\n'.join(current_chapter_lines).strip()
                        if chapter_text:
                            chapter_text = normalize_quotes(chapter_text)
                            output_data.append({
                                'chapter_id': f"chapter_{len(output_data)+1:03d}",
                                'chapter_title': current_chapter_title,
                                'text': chapter_text
                            })
                    current_chapter_title = normalize_quotes(line.strip())
                    current_chapter_lines = []
                    prev_empty_lines = 0
                    skipping_after_title = True
                else:
                    if current_chapter_title is not None:
                        current_chapter_lines.append(line)
                    prev_empty_lines = 0
                    skipping_after_title = False
        
        if current_chapter_title is not None:
            chapter_text = '\n'.join(current_chapter_lines).strip()
            if chapter_text:
                chapter_text = normalize_quotes(chapter_text)
                output_data.append({
                    'chapter_id': f"chapter_{len(output_data)+1:03d}",
                    'chapter_title': current_chapter_title,
                    'text': chapter_text
                })
        
        if not output_data:
            output_data = [{
                'chapter_id': 'chapter_001',
                'chapter_title': 'Chapter 1',
                'text': normalize_quotes(text.strip())
            }]
    else:
        output_data = chapters
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Wrote {len(output_data)} chapters to {output_path}")
    
    # Print summary
    print("\nChapter summary:")
    for i, chapter in enumerate(output_data[:10]):  # Show first 10
        title = chapter.get('chapter_title', 'N/A')
        text_preview = chapter['text'][:50].replace('\n', ' ')
        print(f"  {i+1}. {title} ({len(chapter['text'])} chars)")
        print(f"     Preview: {text_preview}...")
    
    if len(output_data) > 10:
        print(f"  ... and {len(output_data) - 10} more chapters")
    
    return 0


if __name__ == "__main__":
    exit(main())

