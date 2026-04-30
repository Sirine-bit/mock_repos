#!/usr/bin/env python
# etl/run.py - Test case extraction script

import sys
import json

def get_result_tcs_ipnext(data):
    """
    Extract test cases from codebeamer response.
    
    Expected data format:
    {
        "results": [
            {
                "team": {"id": 123},
                "name": "test_case_1"
            }
        ]
    }
    """
    results = []
    
    for item in data.get('results', []):
        # BUG: This assumes 'team' is always a dict, but sometimes it's a list
        team_id = item.get('team').get('id')  # Line 46: AttributeError here when team is a list
        results.append({
            'team_id': team_id,
            'name': item.get('name')
        })
    
    return results

if __name__ == '__main__':
    # Sample data with incorrect structure - team is a list instead of dict
    test_data = {
        "results": [
            {
                "team": [{"id": 123}, {"id": 124}],  # This is a list, not a dict!
                "name": "Test Case 1"
            }
        ]
    }
    
    try:
        tcs = get_result_tcs_ipnext(test_data)
        print(json.dumps(tcs, indent=2))
    except AttributeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
