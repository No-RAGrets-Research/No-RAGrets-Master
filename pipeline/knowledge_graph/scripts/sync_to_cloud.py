#!/usr/bin/env python3
"""
Cloud sync utility to transfer data between local and cloud Dgraph instances.
Supports Dgraph Cloud and self-hosted cloud deployments.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

class DgraphCloudSync:
    def __init__(self, local_endpoint="localhost:8080", cloud_endpoint=None):
        self.local_endpoint = local_endpoint
        self.cloud_endpoint = cloud_endpoint
        
    def export_from_local(self, export_name=None):
        """Export data from local Dgraph instance."""
        if not export_name:
            from datetime import datetime
            export_name = f"local_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        export_dir = Path("exports") / export_name
        export_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Exporting from local Dgraph...")
        
        try:
            # Export schema
            schema_cmd = [
                "curl", "-s", "-X", "POST",
                f"http://{self.local_endpoint}/admin/schema"
            ]
            schema_result = subprocess.run(schema_cmd, capture_output=True, text=True)
            
            if schema_result.returncode == 0:
                with open(export_dir / "schema.json", "w") as f:
                    f.write(schema_result.stdout)
                print("Schema exported")
            
            # Export data in RDF format
            export_cmd = [
                "curl", "-s", "-X", "POST",
                f"http://{self.local_endpoint}/admin/export",
                "-H", "Content-Type: application/json",
                "-d", '{"format": "rdf", "namespace": 0}'
            ]
            
            export_result = subprocess.run(export_cmd, capture_output=True, text=True)
            
            if export_result.returncode == 0:
                response = json.loads(export_result.stdout)
                export_id = response.get('data', {}).get('export', {}).get('response', {}).get('message', '')
                print(f"Data export initiated: {export_id}")
                
                # Note: In production, you'd wait for export completion and download files
                print("Note: Export files will be available in Dgraph's export directory")
                print("    For cloud sync, implement file download and upload logic here")
                
            return str(export_dir)
            
        except Exception as e:
            print(f"Export failed: {e}")
            return None
    
    def import_to_cloud(self, export_dir, cloud_endpoint):
        """Import data to cloud Dgraph instance."""
        if not cloud_endpoint:
            print("❌ Cloud endpoint not specified")
            return False
        
        print(f"Importing to cloud Dgraph at {cloud_endpoint}...")
        
        try:
            # Load schema to cloud
            schema_file = Path(export_dir) / "schema.json"
            if schema_file.exists():
                with open(schema_file) as f:
                    schema_data = f.read()
                
                schema_cmd = [
                    "curl", "-s", "-X", "POST",
                    f"https://{cloud_endpoint}/admin/schema",
                    "-H", "Content-Type: application/json",
                    "-H", f"X-Auth-Token: {os.getenv('DGRAPH_CLOUD_TOKEN', '')}",
                    "-d", schema_data
                ]
                
                schema_result = subprocess.run(schema_cmd, capture_output=True, text=True)
                
                if schema_result.returncode == 0:
                    print("Schema loaded to cloud")
                else:
                    print(f"Schema load failed: {schema_result.stderr}")
                    return False
            
            # Note: In production, implement RDF data upload
            print("Note: Implement RDF data upload for complete sync")
            print("    This would involve uploading .rdf.gz files to cloud instance")
            
            return True
            
        except Exception as e:
            print(f"Cloud import failed: {e}")
            return False
    
    def sync_local_to_cloud(self, cloud_endpoint):
        """Complete sync from local to cloud."""
        # Export from local
        export_dir = self.export_from_local()
        if not export_dir:
            return False
        
        # Import to cloud
        success = self.import_to_cloud(export_dir, cloud_endpoint)
        return success

def main():
    parser = argparse.ArgumentParser(description="Sync Dgraph data between local and cloud")
    parser.add_argument("--local-endpoint", default="localhost:8080", 
                       help="Local Dgraph endpoint")
    parser.add_argument("--cloud-endpoint", required=True,
                       help="Cloud Dgraph endpoint (e.g., your-cluster.grpc.cloud.dgraph.io)")
    parser.add_argument("--direction", choices=["local-to-cloud", "cloud-to-local"], 
                       default="local-to-cloud", help="Sync direction")
    parser.add_argument("--export-only", action="store_true", 
                       help="Only export, don't import")
    
    args = parser.parse_args()
    
    # Check for cloud auth token
    if not os.getenv('DGRAPH_CLOUD_TOKEN') and not args.export_only:
        print("WARNING: Set DGRAPH_CLOUD_TOKEN environment variable for cloud access")
        print("   export DGRAPH_CLOUD_TOKEN=your_token_here")
    
    syncer = DgraphCloudSync(args.local_endpoint, args.cloud_endpoint)
    
    if args.direction == "local-to-cloud":
        if args.export_only:
            result = syncer.export_from_local()
            success = result is not None
        else:
            success = syncer.sync_local_to_cloud(args.cloud_endpoint)
    else:
        print("Cloud-to-local sync not implemented yet")
        success = False
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())