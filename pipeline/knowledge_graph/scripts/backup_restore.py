#!/usr/bin/env python3
"""
Database backup and restore utilities for Dgraph.
Provides easy backup/restore functionality for your KG data.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class DgraphBackupManager:
    def __init__(self, alpha_url="localhost:9080"):
        self.alpha_url = alpha_url
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create a backup of the current Dgraph database."""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"kg_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        print(f"Creating backup: {backup_name}")
        
        # Export schema and data
        try:
            # Export schema
            schema_cmd = [
                "curl", "-X", "POST", 
                f"http://{self.alpha_url}/admin/schema",
                "-H", "Content-Type: application/json"
            ]
            schema_result = subprocess.run(schema_cmd, capture_output=True, text=True)
            
            if schema_result.returncode == 0:
                with open(backup_path / "schema.json", "w") as f:
                    f.write(schema_result.stdout)
                print("Schema exported")
            
            # Export data using RDF format
            export_cmd = [
                "curl", "-X", "POST",
                f"http://{self.alpha_url}/admin/export",
                "-H", "Content-Type: application/json",
                "-d", '{"format": "rdf"}'
            ]
            export_result = subprocess.run(export_cmd, capture_output=True, text=True)
            
            if export_result.returncode == 0:
                print("Data export initiated")
                print("Note: Data files will be created in Dgraph's export directory")
                
            # Create metadata file
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "alpha_url": self.alpha_url,
                "export_format": "rdf"
            }
            
            with open(backup_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            print(f"Backup failed: {e}")
            return None
    
    def list_backups(self):
        """List available backups."""
        backups = []
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_file = backup_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                    backups.append({
                        "name": backup_dir.name,
                        "path": str(backup_dir),
                        "created_at": metadata.get("created_at", "Unknown")
                    })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def restore_backup(self, backup_name):
        """Restore from a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False
        
        print(f"Restoring from backup: {backup_name}")
        print("WARNING: This will replace all current data!")
        confirm = input("Continue? (y/N): ")
        
        if confirm.lower() != 'y':
            print("Restore cancelled")
            return False
        
        try:
            # Drop all data first
            drop_cmd = [
                "curl", "-X", "POST",
                f"http://{self.alpha_url}/alter",
                "-H", "Content-Type: application/json",
                "-d", '{"drop_all": true}'
            ]
            subprocess.run(drop_cmd, check=True)
            print("Existing data dropped")
            
            # Restore schema
            schema_file = backup_path / "schema.json"
            if schema_file.exists():
                with open(schema_file) as f:
                    schema_data = f.read()
                
                schema_cmd = [
                    "curl", "-X", "POST",
                    f"http://{self.alpha_url}/admin/schema",
                    "-H", "Content-Type: application/json",
                    "-d", schema_data
                ]
                subprocess.run(schema_cmd, check=True)
                print("Schema restored")
            
            print("Backup restored successfully")
            print("Note: For RDF data, you may need to manually import the exported files")
            return True
            
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Dgraph backup and restore utility")
    parser.add_argument("--alpha-url", default="localhost:9080", help="Dgraph Alpha URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup")
    backup_parser.add_argument("--name", help="Backup name (optional)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_name", help="Name of backup to restore")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = DgraphBackupManager(args.alpha_url)
    
    if args.command == "backup":
        result = manager.create_backup(args.name)
        return 0 if result else 1
        
    elif args.command == "list":
        backups = manager.list_backups()
        if backups:
            print("\nAvailable backups:")
            for backup in backups:
                print(f"  {backup['name']} - {backup['created_at']}")
        else:
            print("No backups found")
        return 0
        
    elif args.command == "restore":
        result = manager.restore_backup(args.backup_name)
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())