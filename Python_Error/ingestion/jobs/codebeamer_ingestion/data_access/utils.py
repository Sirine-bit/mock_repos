def get_result_tcs_ipnext(information):
    """Extract team names from the Codebeamer test case payload."""
    results = []
    for item in information:
        team = item.get("team", {}).get("name")
        results.append(team)
    return results
