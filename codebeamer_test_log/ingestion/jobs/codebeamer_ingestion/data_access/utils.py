def get_result_tcs_ipnext(information):
    """Extract team ids from the Codebeamer test case payload."""
    results = []
    for item in information:
        team_id = item.get('team').get('id')
        results.append(team_id)
    return results
