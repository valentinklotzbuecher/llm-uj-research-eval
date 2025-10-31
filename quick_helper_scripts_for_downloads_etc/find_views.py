#!/usr/bin/env python3
"""Find views in the Coda document."""

import requests
from pathlib import Path

CODA_API_KEY_FILE = "key/coda_key.txt"
CODA_DOC_ID = "dIEzDONWdb"
RESEARCH_TABLE_ID = "grid-sync-1054-Table-dynamic-ac55549d6df3bbbead8dd779fcad2c0ac3435ec9abfec7a17ef04df988e27cd4"

def load_coda_api_key() -> str:
    key_path = Path(CODA_API_KEY_FILE)
    return key_path.read_text().strip()

def find_views(api_key: str, doc_id: str):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Get all tables and views
    tables_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables"
    response = requests.get(tables_url, headers=headers, params={"limit": 100})

    if response.status_code == 200:
        data = response.json()
        tables = data.get("items", [])

        # Filter for views
        views = [t for t in tables if t.get("tableType") == "view"]

        print(f"Found {len(views)} views:\n")
        for view in views:
            print(f"Name: {view.get('name')}")
            print(f"ID: {view.get('id')}")
            print(f"Parent table: {view.get('parent', {}).get('name', 'N/A')}")
            print()

        # Also check the research table directly for column info
        print(f"\nChecking columns in 'research' table:\n")
        columns_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables/{RESEARCH_TABLE_ID}/columns"
        col_response = requests.get(columns_url, headers=headers, params={"limit": 100})

        if col_response.status_code == 200:
            columns = col_response.json().get("items", [])
            print(f"Found {len(columns)} columns:\n")
            for col in columns[:30]:  # Show first 30
                print(f"  - {col.get('name')} (ID: {col.get('id')})")
        else:
            print(f"Error: {col_response.status_code}")

if __name__ == "__main__":
    api_key = load_coda_api_key()
    find_views(api_key, CODA_DOC_ID)
