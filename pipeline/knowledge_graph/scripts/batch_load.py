#!/usr/bin/env python3
"""
Quick data loading script to batch load all your extracted triples into Dgraph.
Supports both text and visual triples with progress tracking.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from kg_data_loader import KGDataLoader

class BatchKGLoader:
    def __init__(self, verbose=False, force_update=False):
        self.loader = KGDataLoader(verbose=verbose, force_update=force_update)
        self.verbose = verbose
        self.force_update = force_update
        self.stats = {
            'total_files': 0,
            'successful_loads': 0,
            'failed_loads': 0,
            'total_nodes': 0,
            'total_relations': 0,
            'start_time': None,
            'failed_files': []
        }
    
    def discover_kg_files(self, base_dir):
        """Discover all KG result files in the directory structure."""
        base_path = Path(base_dir)
        kg_files = []
        
        # Text triples
        text_dir = base_path / "kg_gen_pipeline" / "output" / "text_triples"
        if text_dir.exists():
            text_files = list(text_dir.glob("*.json"))
            kg_files.extend([(f, "text") for f in text_files])
        
        # Visual triples
        visual_dir = base_path / "kg_gen_pipeline" / "output" / "raw_visual_triples"
        if visual_dir.exists():
            visual_files = list(visual_dir.glob("*_kg_format.json"))
            kg_files.extend([(f, "visual") for f in visual_files])
        
        return kg_files
    
    def load_single_file(self, file_path, file_type):
        """Load a single KG file and track stats."""
        print(f"\nLoading {file_type} triples: {file_path.name}")
        
        try:
            # Get pre-load stats from file
            with open(file_path) as f:
                data = json.load(f)
            
            summary = data.get('summary', {})
            file_entities = summary.get('entities', 0)
            file_relations = summary.get('relations', 0)
            
            print(f"   File contains: {file_entities} entities, {file_relations} relations")
            
            # Load into database
            success = self.loader.load_kg_results(str(file_path))
            
            if success:
                self.stats['successful_loads'] += 1
                self.stats['total_nodes'] += file_entities
                self.stats['total_relations'] += file_relations
                print(f"   Successfully loaded!")
            else:
                self.stats['failed_loads'] += 1
                self.stats['failed_files'].append(str(file_path))
                print(f"   Failed to load")
            
            return success
            
        except Exception as e:
            print(f"   Error loading file: {e}")
            self.stats['failed_loads'] += 1
            self.stats['failed_files'].append(str(file_path))
            return False
    
    def load_all_files(self, base_dir, file_types=None, dry_run=False):
        """Load all discovered KG files."""
        if file_types is None:
            file_types = ["text", "visual"]
        
        # Check database connection
        if not dry_run and not self.loader.manager.health_check():
            print("❌ ERROR: Dgraph is not running. Start it with:")
            print("   cd knowledge_graph && docker compose up -d")
            return False
        
        # Discover files
        kg_files = self.discover_kg_files(base_dir)
        
        # Filter by type if specified
        if file_types:
            kg_files = [(f, t) for f, t in kg_files if t in file_types]
        
        self.stats['total_files'] = len(kg_files)
        self.stats['start_time'] = datetime.now()
        
        print(f"\nStarting batch load of {len(kg_files)} KG files...")
        print(f"   Types: {', '.join(file_types)}")
        
        if dry_run:
            print("   DRY RUN - No data will be loaded")
        elif self.verbose:
            print("   VERBOSE MODE - Will show skipped items")
        elif self.force_update:
            print("   FORCE UPDATE MODE - Will overwrite existing data")
        
        # Process files
        for i, (file_path, file_type) in enumerate(kg_files, 1):
            print(f"\n[{i}/{len(kg_files)}]", end=" ")
            
            if dry_run:
                print(f"Would load {file_type} triples: {file_path.name}")
                continue
            
            self.load_single_file(file_path, file_type)
        
        self.print_summary()
        return self.stats['failed_loads'] == 0
    
    def print_summary(self):
        """Print loading summary statistics."""
        end_time = datetime.now()
        duration = end_time - self.stats['start_time'] if self.stats['start_time'] else None
        
        print("\n" + "="*60)
        print("BATCH LOADING SUMMARY")
        print("="*60)
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Successful loads: {self.stats['successful_loads']}")
        print(f"Failed loads: {self.stats['failed_loads']}")
        print(f"Total nodes loaded: {self.stats['total_nodes']:,}")
        print(f"Total relations loaded: {self.stats['total_relations']:,}")
        
        if duration:
            print(f"Total time: {duration}")
            
        if self.stats['failed_files']:
            print(f"\nFailed files:")
            for failed_file in self.stats['failed_files']:
                print(f"   {failed_file}")
        
        success_rate = (self.stats['successful_loads'] / self.stats['total_files'] * 100) if self.stats['total_files'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")

def main():
    parser = argparse.ArgumentParser(description="Batch load KG data into Dgraph")
    parser.add_argument("--base-dir", default=".", help="Base directory to search for KG files")
    parser.add_argument("--types", nargs="+", choices=["text", "visual"], 
                       help="Types of files to load (default: both)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be loaded without loading")
    parser.add_argument("--clear-first", action="store_true", help="Clear database before loading")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show what items are being skipped")
    parser.add_argument("--force-update", action="store_true",
                       help="Overwrite existing papers/nodes/relations")
    
    args = parser.parse_args()
    
    if args.force_update and not args.dry_run:
        print("WARNING: Force update mode will overwrite existing data!")
        confirm = input("Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return 1
    
    loader = BatchKGLoader(args.verbose, args.force_update)
    
    # Clear database if requested
    if args.clear_first and not args.dry_run:
        print("WARNING: Clearing database first...")
        confirm = input("This will delete all existing data. Continue? (y/N): ")
        if confirm.lower() == 'y':
            try:
                import subprocess
                drop_cmd = [
                    "curl", "-X", "POST",
                    "http://localhost:8080/alter",
                    "-H", "Content-Type: application/json",
                    "-d", '{"drop_all": true}'
                ]
                subprocess.run(drop_cmd, check=True)
                print("Database cleared")
            except Exception as e:
                print(f"Failed to clear database: {e}")
                return 1
        else:
            print("Operation cancelled")
            return 1
    
    # Run batch loading
    success = loader.load_all_files(args.base_dir, args.types, args.dry_run)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())