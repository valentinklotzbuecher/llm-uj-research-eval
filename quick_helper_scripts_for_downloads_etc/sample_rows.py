#!/usr/bin/env python3
"""Get sample rows from research table to see structure."""

import requests
import json
from pathlib import Path

CODA_API_KEY_FILE = "key/coda_key.txt"
CODA_DOC_ID = "dIEzDONWdb"
RESEARCH_TABLE_ID = "grid-sync-1054-Table-dynamic-ac55549d6df3bbbead8dd779fcad2c0ac3435ec9abfec7a17ef04df988e27cd4"

def load_coda_api_key() -> str:
    key_path = Path(CODA_API_KEY_FILE)
    return key_path.read_text().strip()

def get_sample_rows(api_key: str, doc_id: str, table_id: str):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Get first few rows
    rows_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables/{table_id}/rows"
    response = requests.get(rows_url, headers=headers, params={
        "useColumnNames": True,
        "limit": 3
    })

    if response.status_code == 200:
        data = response.json()
        rows = data.get("items", [])

        print(f"Found {len(rows)} sample rows\n")
        print("=" * 80)

        for i, row in enumerate(rows, 1):
            print(f"\nROW {i}:")
            print("-" * 80)
            values = row.get("values", {})

            # Print all column values
            for key, value in values.items():
                if isinstance(value, dict):
                    # Extract meaningful data from dict
                    display = value.get("name") or value.get("value") or str(value)
                else:
                    display = value

                # Truncate long values
                if isinstance(display, str) and len(display) > 100:
                    display = display[:100] + "..."

                print(f"  {key}: {display}")

            print("=" * 80)

        # Also print raw JSON for first row
        if rows:
            print("\n\nRAW JSON for first row:")
            print(json.dumps(rows[0], indent=2))

    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    api_key = load_coda_api_key()
    get_sample_rows(api_key, CODA_DOC_ID, RESEARCH_TABLE_ID)
