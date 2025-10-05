#!/usr/bin/env python
"""
Export the OpenAPI schema from the FastAPI app to a JSON file.
This is used for generating TypeScript SDK in the frontend.
"""
import json
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and configure the app
from main import app

def export_openapi_schema():
    """Export the OpenAPI schema to a JSON file."""
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Output the schema as JSON to stdout
    print(json.dumps(openapi_schema, indent=2))

if __name__ == "__main__":
    export_openapi_schema()
