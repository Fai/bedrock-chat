#!/usr/bin/env python3
"""
Standalone script to sync Redshift schema to Bedrock SQL Knowledge Base.
This can be run manually or scheduled via EventBridge.

Usage:
    python sync_schema.py <knowledge_base_id> <workgroup_name> <database>

Example:
    python sync_schema.py 5YFO60KIDN icon-framework dev
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sql_kb_schema_sync import sync_sql_kb_schema


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python sync_schema.py <kb_id> <workgroup_name> <database> [schema] [region]")
        print("\nExample:")
        print("  python sync_schema.py 5YFO60KIDN icon-framework dev")
        sys.exit(1)

    kb_id = sys.argv[1]
    workgroup = sys.argv[2]
    database = sys.argv[3]
    schema = sys.argv[4] if len(sys.argv) > 4 else "public"
    region = sys.argv[5] if len(sys.argv) > 5 else "us-east-1"

    print(f"Syncing schema for KB: {kb_id}")
    print(f"Workgroup: {workgroup}")
    print(f"Database: {database}")
    print(f"Schema: {schema}")
    print(f"Region: {region}")
    print()

    try:
        sync_sql_kb_schema(
            knowledge_base_id=kb_id,
            workgroup_name=workgroup,
            database=database,
            schema=schema,
            region=region
        )
        print("\n✓ Schema sync completed successfully!")
    except Exception as e:
        print(f"\n✗ Schema sync failed: {e}")
        sys.exit(1)
