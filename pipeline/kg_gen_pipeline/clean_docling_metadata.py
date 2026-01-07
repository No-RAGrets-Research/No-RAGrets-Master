"""
Clean "Copy of" from Docling JSON metadata fields.

This script updates the internal metadata in Docling JSON files to remove
"Copy of " prefix from the 'name' and 'filename' fields in the origin section.
"""

import json
from pathlib import Path


def clean_docling_json(json_path: Path) -> bool:
    """
    Remove "Copy of " prefix from metadata fields in a Docling JSON file.
    
    Args:
        json_path: Path to Docling JSON file
        
    Returns:
        True if file was modified, False otherwise
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    modified = False
    
    # Clean the 'name' field at top level
    if 'name' in data and data['name'].startswith('Copy of '):
        data['name'] = data['name'][8:]  # Remove "Copy of " (8 characters)
        modified = True
        print(f"  - Cleaned 'name' field")
    
    # Clean the 'origin' section
    if 'origin' in data:
        if 'filename' in data['origin'] and data['origin']['filename'].startswith('Copy of '):
            data['origin']['filename'] = data['origin']['filename'][8:]
            modified = True
            print(f"  - Cleaned 'origin.filename' field")
    
    # Write back if modified
    if modified:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    
    return False


def main():
    """Process all Docling JSON files."""
    docling_dir = Path(__file__).parent / "output" / "docling_json"
    
    if not docling_dir.exists():
        print(f"Error: Directory not found: {docling_dir}")
        return
    
    json_files = list(docling_dir.glob("*.json"))
    print(f"Found {len(json_files)} Docling JSON files\n")
    
    modified_count = 0
    
    for json_path in sorted(json_files):
        print(f"Processing: {json_path.name}")
        if clean_docling_json(json_path):
            modified_count += 1
        else:
            print(f"  - No 'Copy of' found")
    
    print(f"\n✅ Complete! Modified {modified_count} / {len(json_files)} files")


if __name__ == "__main__":
    main()
