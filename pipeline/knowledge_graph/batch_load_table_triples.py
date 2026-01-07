#!/usr/bin/env python3
"""Batch load all table triples to Dgraph."""

import subprocess
from pathlib import Path
import json

def main():
    table_triples_dir = Path(__file__).parent.parent / "kg_gen_pipeline" / "output" / "table_triples"
    
    # Find all table triple files
    table_files = sorted(table_triples_dir.glob("*_tables_only_kg_format_*.json"))
    
    # Skip the summary file
    table_files = [f for f in table_files if 'extraction_summary' not in f.name]
    
    print(f"Found {len(table_files)} table triple files to load")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, file_path in enumerate(table_files, 1):
        print(f"\n[{i}/{len(table_files)}] Loading {file_path.name}...")
        
        try:
            result = subprocess.run(
                ["python", "kg_data_loader.py", str(file_path)],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                success_count += 1
                print(f"✅ Success")
            else:
                error_count += 1
                error_msg = result.stderr or result.stdout
                print(f"❌ Failed: {error_msg}")
                errors.append({
                    'file': file_path.name,
                    'error': error_msg
                })
        except subprocess.TimeoutExpired:
            error_count += 1
            print(f"❌ Timeout")
            errors.append({
                'file': file_path.name,
                'error': 'Timeout after 60s'
            })
        except Exception as e:
            error_count += 1
            print(f"❌ Exception: {e}")
            errors.append({
                'file': file_path.name,
                'error': str(e)
            })
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {error_count}")
    
    if errors:
        print(f"\nErrors:")
        for error in errors:
            print(f"  - {error['file']}: {error['error']}")
        
        # Save errors to file
        error_file = table_triples_dir / "loading_errors.json"
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        print(f"\nErrors saved to: {error_file}")

if __name__ == "__main__":
    main()
