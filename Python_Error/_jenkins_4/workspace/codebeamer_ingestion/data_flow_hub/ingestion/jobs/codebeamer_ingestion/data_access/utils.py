import pandas as pd
import requests

def get_result_tcs_ipnext(information):
    """
    Extracts test case name and team information.
    """
    results = []
    for item in information:
        team = item.get("team", {}).get("name")
        results.append(team)
    return results

def other_util():
    pass

