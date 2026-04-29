import pandas as pd


def extract_requirements():
    rows = [
        {
            "tracker": "A05_System Requirements",
            "tracker_id": 34158092,
            "assigned_to": ", ".join(
                [
                    "q477433",
                    "q560470",
                    "qxz4zdz",
                    "qxz57it",
                    "qxz6j0f",
                    "qxz44kv",
                    "qxz4z31",
                    "qxz5rqi",
                    "qxz5bgs",
                    "qxz6ine",
                    "q549798",
                    "q551230",
                ]
            ),
        }
    ]
    return pd.DataFrame(rows)
