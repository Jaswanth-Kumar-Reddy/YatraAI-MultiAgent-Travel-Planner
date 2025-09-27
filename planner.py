# planner.py
import argparse
import json
import os
from flask import Flask, request, jsonify
from agents import IngestAgent, TrainAgent, BusAgent, ConnectorAgent, PlannerAgent, RankingAgent, FlightAgent
from dotenv import load_dotenv

app = Flask(__name__)

def run_query(query_json, mode="static"):
    """
    Main query function that can use either traditional agents or LangGraph workflow
    """
    # Check if LLM mode is requested
    if mode == "llm" or mode == "langgraph":
        return run_llm_query(query_json)
    else:
        return run_traditional_query(query_json, mode)

def _has_llm_config():
    """Check if LLM configuration is available"""
    return (os.getenv('OPENAI_API_KEY') is not None or 
            os.getenv('ANTHROPIC_API_KEY') is not None)

def run_llm_query(query_json):
    """Run query using LangGraph workflow with LLM agents"""
    try:
        from langgraph_workflow import get_workflow
        
        # Get the workflow instance
        workflow = get_workflow()
        
        # Run the LangGraph workflow
        result = workflow.run_planning_workflow(query_json)
        
        return result
        
    except ImportError as e:
        return {
            "query": query_json,
            "error": f"LangGraph dependencies not installed: {str(e)}",
            "itineraries": [],
            "sources": [{"name": "error", "url": "local", "access": "none"}]
        }
    except Exception as e:
        return {
            "query": query_json,
            "error": f"LLM workflow error: {str(e)}",
            "itineraries": [],
            "sources": [{"name": "error", "url": "local", "access": "none"}]
        }

def run_traditional_query(query_json, mode="static"):
    """Run query using traditional rule-based agents (original implementation)"""
    # 1) Ingest -> split plan into mode queries
    ingest = IngestAgent()
    plan = ingest.run(query_json)

    # 2) For each requested mode, call the relevant agent
    train_legs = []
    bus_legs = []
    flight_legs = []
    other_legs = []
    for item in plan:
        if item["mode"] == "train":
            train_legs.extend(TrainAgent(mode=mode).run(item))
        elif item["mode"] == "bus":
            bus_legs.extend(BusAgent(mode=mode).run(item))
        elif item["mode"] == "flight":
            flight_legs.extend(FlightAgent(mode=mode).run(item))
        else:
            other_legs.append(item)

    # 3) Compute connector legs (taxi/walk) between edges
    connector = ConnectorAgent(mode=mode)
    connectors = connector.run(bus_legs + train_legs)

    # 4) Planner stitches into multiple itineraries
    planner = PlannerAgent()
    itineraries = planner.run(bus_legs, connectors, train_legs, flight_legs)

    # 5) Ranking - rank each itinerary
    ranking_agent = RankingAgent()
    ranked_itineraries = []
    
    for itinerary in itineraries:
        ranked = ranking_agent.run(itinerary, query_json.get("preferences", {}))
        ranked_itineraries.append(ranked)
    
    # Sort by overall score (highest first)
    ranked_itineraries.sort(key=lambda x: x.get("score", {}).get("overall", 0), reverse=True)

    # Add comprehensive disclaimers based on mode
    if mode == "static":
        data_disclaimer = {
            "data_type": "DEMO_DATA_ONLY",
            "disclaimer": "⚠️ STATIC MODE: Using realistic demo data for demonstration purposes.",
            "data_sources": {
                "trains": "Static demo data with realistic train names and schedules",
                "flights": "Static demo data with realistic airline and flight numbers",
                "buses": "Static demo data with realistic routes and timings",
                "metro": "Static demo data for supported cities"
            },
            "limitations": {
                "booking": "Demo data only - cannot make actual reservations",
                "real_time": "No live data - all information is for demonstration",
                "accuracy": "Data is realistic but not current or bookable"
            },
            "purpose": "Demonstrates system architecture and planning capabilities"
        }
    elif mode == "hybrid":
        data_disclaimer = {
            "data_type": "HYBRID_REAL_AND_DEMO",
            "disclaimer": "🔄 HYBRID MODE: Uses free/community APIs for real data where available, demo data as fallback.",
            "data_sources": {
                "trains": "Railway MCP server (live) → demo fallback",
                "flights": "OpenSky Network (live) → demo fallback", 
                "buses": "Regional APIs (Delhi DTC, Bangalore BMTC) → demo fallback",
                "metro": "City-specific APIs (Delhi Metro) → demo fallback"
            },
            "real_data_coverage": {
                "trains": "Live data for major routes via Railway MCP",
                "flights": "Live aircraft tracking via OpenSky Network",
                "buses": "Regional coverage only (Delhi, Bangalore)",
                "pricing": "Mix of real and estimated pricing"
            },
            "limitations": {
                "booking": "Planning only - cannot make actual reservations",
                "coverage": "Real data limited by free API quotas and regional coverage",
                "accuracy": "Real data subject to API availability and rate limits"
            },
            "api_status": "Check console logs to see which APIs provided real vs demo data",
            "for_demonstration": "Shows integration of real free APIs with intelligent fallbacks"
        }
    elif mode == "api":
        data_disclaimer = {
            "data_type": "API_MODE_REALISTIC",
            "disclaimer": "🔌 API MODE: Attempts real API calls with realistic demo fallbacks.",
            "data_sources": {
                "trains": "Railway APIs → realistic demo fallback",
                "flights": "Flight APIs → realistic demo fallback",
                "buses": "Bus operator APIs → realistic demo fallback"
            },
            "limitations": {
                "booking": "Planning only - cannot make actual reservations",
                "api_keys": "Requires valid API keys for real data",
                "fallback": "Falls back to realistic demo when APIs unavailable"
            },
            "purpose": "Demonstrates API integration patterns with fallbacks"
        }
    else:  # Default fallback
        data_disclaimer = {
            "data_type": "DEMO_DATA_FALLBACK",
            "disclaimer": "⚠️ Using demo data - mode not fully configured.",
            "purpose": "Fallback demonstration mode"
        }
    
    result = {
        "query": query_json,
        "itineraries": ranked_itineraries,
        "sources": [
            {"name": "traditional_agents", "url": "local", "access": "rule_based"}
        ],
        "data_disclaimer": data_disclaimer
    }
    return result

@app.route("/plan", methods=["POST"])
def plan_http():
    query_json = request.get_json()
    mode = query_json.get("mode", "static")
    return jsonify(run_query(query_json, mode=mode))

def main_cli():
    # Load environment variables from .env, if present
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="frm", required=True)
    parser.add_argument("--to", dest="to", required=True)
    parser.add_argument("--date", dest="date", required=True)
    parser.add_argument(
        "--mode",
        dest="mode",
        default="auto",
        choices=["auto", "llm", "langgraph", "api", "static"],
        help="Planning mode: auto (default), llm/langgraph (LLM agents), api/static (traditional)"
    )
    args = parser.parse_args()
    # Auto-detect mode for CLI if requested
    mode = args.mode
    if mode == "auto":
        mode = "llm" if _has_llm_config() else "api"
    query = {
        "from": args.frm,
        "to": args.to,
        "date": args.date,
        "preferences": {"prioritize": "cost", "max_transfers": 3}
    }
    result = run_query(query, mode=mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main_cli()
