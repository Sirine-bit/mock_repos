import sys
import os
import json

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def run_extraction():
    print("Starting extraction for testguide ipnext testcases...")
    
    # Intentionally failing code block with a glaring typo (NameError)
    # The variable ticket_ids is never defined, breaking the loop.
    extracted_data = []
    
    # The typo here is the root cause of the downstream job failing.
    # The variable should be `sys.argv[1:]` or a predefined list, but instead it is undefined context.
    try:
        for t_id in tcket_ids:  # FATAL: tcket_ids is not defined!
            extracted_data.append({"id": t_id, "status": "extracted"})
    except NameError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
        
    print(f"Successfully extracted {len(extracted_data)} testcases.")

if __name__ == "__main__":
    run_extraction()
