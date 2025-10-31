#!/usr/bin/env python3
"""Explore Coda document structure to find the Papers table."""

import requests
from pathlib import Path

CODA_API_KEY_FILE = "key/coda_key.txt"
CODA_DOC_ID = "dIEzDONWdb"

def load_coda_api_key() -> str:
    """Load Coda API key from file."""
    key_path = Path(CODA_API_KEY_FILE)
    return key_path.read_text().strip()

def explore_doc(api_key: str, doc_id: str):
    """Explore document pages and search for papers table."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # List pages
    pages_url = f"https://coda.io/apis/v1/docs/{doc_id}/pages"
    print(f"Fetching pages from: {pages_url}\n")
    response = requests.get(pages_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        pages = data.get("items", [])
        print(f"Found {len(pages)} pages:\n")
        for page in pages:
            print(f"  Name: {page.get('name')}")
            print(f"  ID: {page.get('id')}")
            print(f"  Type: {page.get('type')}")
            print()
    else:
        print(f"Error: {response.status_code} - {response.text}")

    # Search for a table with "paper" in the name
    print("\nSearching all tables for 'paper' keyword:\n")
    tables_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables"
    response = requests.get(tables_url, headers=headers, params={"limit": 100})

    if response.status_code == 200:
        data = response.json()
        tables = data.get("items", [])

        paper_tables = [t for t in tables if "paper" in t.get("name", "").lower()]

        if paper_tables:
            print(f"Found {len(paper_tables)} tables with 'paper' in name:\n")
            for table in paper_tables:
                print(f"  Name: {table.get('name')}")
                print(f"  ID: {table.get('id')}")
                print(f"  Type: {table.get('tableType')}")
                print()
        else:
            print("No tables found with 'paper' in name")
            print("\nTrying to search in 'research' table (ID: grid-sync-1054-Table-dynamic-ac55549d6df3bbbead8dd779fcad2c0ac3435ec9abfec7a17ef04df988e27cd4)...")

            # The 'research' table from "All evaluations (filterable)" might be what we need
            research_table_id = "grid-sync-1054-Table-dynamic-ac55549d6df3bbbead8dd779fcad2c0ac3435ec9abfec7a17ef04df988e27cd4"

            # Get columns
            columns_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables/{research_table_id}/columns"
            col_response = requests.get(columns_url, headers=headers)

            if col_response.status_code == 200:
                columns = col_response.json().get("items", [])
                print(f"\nColumns in 'research' table ({len(columns)} total):\n")
                for col in columns:
                    print(f"  - {col.get('name')} (ID: {col.get('id')})")
            else:
                print(f"Error fetching columns: {col_response.status_code}")

if __name__ == "__main__":
    api_key = load_coda_api_key()
    explore_doc(api_key, CODA_DOC_ID)
