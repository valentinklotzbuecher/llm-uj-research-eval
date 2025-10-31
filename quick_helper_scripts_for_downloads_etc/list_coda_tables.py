#!/usr/bin/env python3
"""Helper script to list all tables in a Coda document."""

import requests
from pathlib import Path

CODA_API_KEY_FILE = "key/coda_key.txt"
CODA_DOC_ID = "dIEzDONWdb"

def load_coda_api_key() -> str:
    """Load Coda API key from file."""
    key_path = Path(CODA_API_KEY_FILE)
    if not key_path.exists():
        raise FileNotFoundError(f"Coda API key not found at {CODA_API_KEY_FILE}")
    return key_path.read_text().strip()

def list_tables(api_key: str, doc_id: str):
    """List all tables in a Coda document."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # First, get document info
    doc_url = f"https://coda.io/apis/v1/docs/{doc_id}"
    print(f"Fetching document info from: {doc_url}")
    doc_response = requests.get(doc_url, headers=headers)

    if doc_response.status_code == 200:
        doc_data = doc_response.json()
        print(f"\nDocument: {doc_data.get('name')}")
        print(f"ID: {doc_data.get('id')}")
    else:
        print(f"Error fetching document: {doc_response.status_code}")
        print(doc_response.text)
        return

    # List all tables
    tables_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables"
    print(f"\nFetching tables from: {tables_url}")
    response = requests.get(tables_url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    tables = data.get("items", [])

    print(f"\nFound {len(tables)} tables:\n")
    for i, table in enumerate(tables, 1):
        print(f"{i}. Name: {table.get('name')}")
        print(f"   ID: {table.get('id')}")
        print(f"   Type: {table.get('tableType')}")
        print(f"   Parent: {table.get('parent', {}).get('name', 'N/A')}")
        print()

if __name__ == "__main__":
    api_key = load_coda_api_key()
    list_tables(api_key, CODA_DOC_ID)
