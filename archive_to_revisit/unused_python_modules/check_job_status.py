#!/usr/bin/env python3
"""Quick script to check job status and retrieve error details."""

import os
import pathlib
from openai import OpenAI

API_KEY_PATH = pathlib.Path("key/openai_key.txt")
if os.getenv("OPENAI_API_KEY") is None and API_KEY_PATH.exists():
    os.environ["OPENAI_API_KEY"] = API_KEY_PATH.read_text().strip()

client = OpenAI()

# Response IDs from jobs_index.csv
response_ids = {
    "Schuett et al. 2023": "resp_00d4ae6e8394ba9500690a9796956081a2b7282bce5939c909",
    "Williams et al. 2024": "resp_0baa161d57c9f00300690a97981ae08193a86dd994d10d274f"
}

print("Checking job status...\n")
for paper, resp_id in response_ids.items():
    print(f"Paper: {paper}")
    print(f"Response ID: {resp_id}")
    try:
        r = client.responses.retrieve(resp_id)

        # Get status
        status = getattr(r, 'status', 'unknown')
        print(f"Status: {status}")

        # Get error details if available
        if hasattr(r, 'incomplete_details'):
            details = r.incomplete_details
            print(f"Incomplete details: {details}")

        # Get usage if completed
        if hasattr(r, 'usage'):
            usage = r.usage
            print(f"Usage: {usage}")

        # Try to get output if available
        if status == 'completed' and hasattr(r, 'output_text'):
            print(f"Output length: {len(r.output_text)} chars")

    except Exception as e:
        print(f"Error retrieving response: {e}")

    print("-" * 60)
