# utils.py
import json
from datetime import datetime
from dateutil import parser

def load_demo_for_query(frm, to, date):
    with open("data/sample_itineraries.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for route in data.get("demo_routes", []):
        if route["from"].lower().startswith(frm.lower().split(",")[0]) and route["to"].lower().startswith(to.lower().split(",")[0]):
            return route
    return None

def iso_to_dt(s):
    return parser.isoparse(s)

def dt_to_iso(dt):
    return dt.isoformat()
