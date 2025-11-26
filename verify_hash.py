
import hashlib
import json
from pathlib import Path

# The expected hash from src/saaaaaa/core/orchestrator/questionnaire.py
EXPECTED_HASH = "27f7f784583d637158cb70ee236f1a98f77c1a08366612b5ae11f3be24062658"

# Path to the questionnaire monolith
QUESTIONNAIRE_PATH = Path("data/questionnaire_monolith.json")

def compute_hash(data: dict) -> str:
    """Computes the SHA-256 hash of a dictionary in a deterministic way."""
    canonical_json = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

def main():
    """Reads the questionnaire, computes its hash, and compares it to the expected hash."""
    if not QUESTIONNAIRE_PATH.exists():
        print(f"Error: Questionnaire file not found at {QUESTIONNAIRE_PATH}")
        return

    try:
        content = QUESTIONNAIRE_PATH.read_text(encoding='utf-8')
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in questionnaire file: {e}")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    calculated_hash = compute_hash(data)

    print(f"Expected hash:   {EXPECTED_HASH}")
    print(f"Calculated hash: {calculated_hash}")

    if calculated_hash == EXPECTED_HASH:
        print("\nSuccess: The calculated hash matches the expected hash.")
    else:
        print("\nFailure: The calculated hash does not match the expected hash.")

if __name__ == "__main__":
    main()
