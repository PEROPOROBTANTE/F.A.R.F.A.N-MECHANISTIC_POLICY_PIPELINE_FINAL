
import json
import os

# Using relative path within the project
MONOLITH_PATH = 'data/questionnaire_monolith.json'

# This is the inverse of the hardcoded dict in signal_aliasing.py
LEGACY_FINGERPRINTS_TO_ADD = {
    "PA07": "pa07_v1_land_territory",
    "PA08": "pa08_v1_leaders_defenders",
    "PA09": "pa09_v1_prison_rights",
    "PA10": "pa10_v1_migration",
}

def add_legacy_fingerprints():
    """
    Adds the 'legacy_fingerprint' field to the specified policy areas
    in the questionnaire_monolith.json file.
    """
    if not os.path.exists(MONOLITH_PATH):
        print(f"Error: The file {MONOLITH_PATH} was not found in the current directory.")
        return

    try:
        with open(MONOLITH_PATH, 'r', encoding='utf-8') as f:
            monolith_data = json.load(f)
        
        print("Successfully loaded questionnaire_monolith.json")

        policy_areas = monolith_data.get("canonical_notation", {}).get("policy_areas", {})
        
        if not policy_areas:
            print("Error: Could not find 'canonical_notation.policy_areas' in the JSON structure.")
            return

        updated_count = 0
        for pa_id, fingerprint in LEGACY_FINGERPRINTS_TO_ADD.items():
            if pa_id in policy_areas:
                if "legacy_fingerprint" not in policy_areas[pa_id]:
                    policy_areas[pa_id]["legacy_fingerprint"] = fingerprint
                    print(f"Added legacy_fingerprint to {pa_id}")
                    updated_count += 1
                else:
                    # If it exists, let's make sure it's correct
                    if policy_areas[pa_id]["legacy_fingerprint"] != fingerprint:
                         policy_areas[pa_id]["legacy_fingerprint"] = fingerprint
                         print(f"Corrected legacy_fingerprint for {pa_id}")
                         updated_count += 1
                    else:
                         print(f"legacy_fingerprint for {pa_id} is already correct. No change made.")

            else:
                print(f"Warning: Policy area {pa_id} not found in monolith.")

        if updated_count > 0:
            # Use a temporary file for atomic write
            temp_path = MONOLITH_PATH + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(monolith_data, f, ensure_ascii=False, indent=2)
            
            os.replace(temp_path, MONOLITH_PATH)
            print(f"Successfully updated {updated_count} policy areas and saved the file.")
        else:
            print("No updates were necessary.")

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {MONOLITH_PATH}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_legacy_fingerprints()
