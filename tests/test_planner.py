# tests/test_planner.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planner import run_query

def test_static_demo():
    q = {"from":"Mandi, Himachal Pradesh, India","to":"Anantapur, Andhra Pradesh, India","date":"2025-10-03", "preferences": {"prioritize":"cost"}}
    res = run_query(q, mode="static")
    assert "itineraries" in res
    assert len(res["itineraries"]) == 1
    itn = res["itineraries"][0]
    assert "legs" in itn
