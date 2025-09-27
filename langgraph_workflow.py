# langgraph_workflow.py
import os
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# State definition for the travel planning workflow
class TravelPlanState(TypedDict):
    """State that gets passed between agents in the workflow"""
    # Input query
    query: Dict[str, Any]
    
    # Messages for conversation history
    messages: List[Any]
    
    # Agent outputs
    transport_modes: List[Dict[str, Any]]  # From IngestAgent
    flight_options: List[Dict[str, Any]]   # From FlightAgent
    train_options: List[Dict[str, Any]]    # From TrainAgent
    bus_options: List[Dict[str, Any]]      # From BusAgent
    connector_options: List[Dict[str, Any]] # From ConnectorAgent
    
    # Final outputs
    itineraries: List[Dict[str, Any]]      # From PlannerAgent
    ranked_itineraries: List[Dict[str, Any]] # From RankingAgent
    
    # Workflow control
    current_step: str
    error: Optional[str]

class LLMConfig:
    """Configuration for LLM models"""
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.model_provider = os.getenv('LLM_PROVIDER', 'google')  # 'openai', 'anthropic', or 'google'
        self.model_name = os.getenv('LLM_MODEL', 'gemini-1.5-flash')
        self.debug_mode = str(os.getenv('DEBUG_MODE', 'false')).lower() == 'true'
    
    class _MockResponse:
        def __init__(self, content: str):
            self.content = content
    
    class MockChatModel:
        """Simple deterministic mock to emulate Chat model behavior for offline/dev mode"""
        def __init__(self):
            self.is_mock = True
        
        def invoke(self, messages):
            # messages can be a list of HumanMessage/SystemMessage etc.
            # Extract concatenated text for simple routing
            try:
                text = "\n".join([getattr(m, 'content', str(m)) for m in messages])
            except Exception:
                text = str(messages)
            t = text.lower()
            # Health/Connectivity quick check
            if "respond with just 'ok'" in t or "respond with just \"ok\"" in t:
                return LLMConfig._MockResponse("OK")
            # Ingest prompt detection
            if "plan transportation for this travel query" in t:
                # naive parse of From/To/Date
                def _extract(tag):
                    for line in text.splitlines():
                        if line.strip().startswith(f"{tag}:"):
                            return line.split(":",1)[1].strip()
                    return ""
                frm = _extract("From")
                to = _extract("To")
                date = _extract("Date")
                mock = [
                    {"mode": "train", "from": frm, "to": to, "date": date, "priority": "high", "reasoning": "Mock: reasonable distance for train"},
                    {"mode": "bus", "from": frm, "to": to, "date": date, "priority": "medium", "reasoning": "Mock: add bus alternative"}
                ]
                return LLMConfig._MockResponse(json.dumps(mock))
            # Planner prompt detection
            if "plan optimized itineraries using these transportation options" in t:
                # Return a single combined itinerary consuming provided options where possible
                try:
                    # Extremely small synthetic response
                    itinerary = [{
                        "id": "itn-mock-1",
                        "legs": [],
                        "total_estimated_time_min": 0,
                        "total_estimated_cost_inr": 0,
                        "transfer_instructions": ["Mock transfers computed"],
                        "notes": ["Mock itinerary for offline mode"],
                        "optimization_strategy": "balanced"
                    }]
                    return LLMConfig._MockResponse(json.dumps(itinerary))
                except Exception:
                    return LLMConfig._MockResponse("[]")
            # Ranking prompt detection
            if "rank these itineraries based on user preferences" in t:
                # Try to find the ITINERARIES: block json
                try:
                    # naive: find last '{' and form json; fallback to empty
                    ranked = []
                    # Provide a minimal ranked structure to satisfy UI
                    ranked = [{
                        "id": "itn-mock-1",
                        "legs": [],
                        "total_estimated_time_min": 0,
                        "total_estimated_cost_inr": 0,
                        "transfer_instructions": ["Mock transfers computed"],
                        "notes": ["Mock itinerary for offline mode"],
                        "optimization_strategy": "balanced",
                        "score": {"cost": 0.9, "time": 0.9, "comfort": 0.8, "convenience": 0.8, "overall": 0.86},
                        "rank": 1,
                        "ranking_explanation": "Mock ranking in offline mode",
                        "recommendations": ["Provide real API keys for live ranking"]
                    }]
                    return LLMConfig._MockResponse(json.dumps(ranked))
                except Exception:
                    return LLMConfig._MockResponse("[]")
            # Default generic response
            return LLMConfig._MockResponse("OK")
    
    def has_real_llm_config(self):
        """Check if real LLM configuration is available"""
        return (self.openai_api_key is not None or 
                self.anthropic_api_key is not None or 
                self.google_api_key is not None)
        
    def get_llm(self):
        """Get the configured LLM instance"""
        if self.model_provider == 'google' and self.google_api_key:
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.google_api_key,
                temperature=0.1,
                convert_system_message_to_human=True  # Gemini compatibility
            )
        elif self.model_provider == 'anthropic' and self.anthropic_api_key:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                anthropic_api_key=self.anthropic_api_key,
                temperature=0.1
            )
        elif self.model_provider == 'openai' and self.openai_api_key:
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.openai_api_key,
                temperature=0.1
            )
        else:
            # Use mock model in offline/dev mode
            return LLMConfig.MockChatModel()

class LLMIngestAgent:
    """LLM-powered agent for intelligent travel mode selection"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.is_mock = getattr(self.llm, "is_mock", False)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planning agent specializing in transportation mode selection for India.

Your task is to analyze a travel query and determine the optimal transportation modes based on:
1. Distance between locations
2. Available transportation options in India
3. Travel time preferences
4. Cost considerations
5. Practical connectivity

For Indian travel, consider these guidelines:
- Same city (0-50km): Bus, taxi, metro
- Medium distance (50-300km): Bus, train
- Long distance (300-800km): Train (preferred), bus
- Very long distance (800km+): Flight (preferred), train

Major Indian cities with airports: Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad, Jaipur, Chandigarh

Respond with a JSON array of transportation mode requests, each containing:
- mode: "flight", "train", "bus", or "taxi"
- from: origin location
- to: destination location  
- date: travel date
- priority: "high", "medium", "low" (based on suitability)
- reasoning: brief explanation for this mode choice

Example response:
[
  {
    "mode": "train",
    "from": "New Delhi, Delhi, India",
    "to": "Mumbai, Maharashtra, India", 
    "date": "2025-01-15",
    "priority": "high",
    "reasoning": "Long distance route with excellent train connectivity"
  }
]"""),
            ("human", "Plan transportation for this travel query:\n\nFrom: {from_location}\nTo: {to_location}\nDate: {date}\nPreferences: {preferences}")
        ])
    
    def run(self, state: TravelPlanState) -> TravelPlanState:
        """Analyze travel query and determine optimal transportation modes"""
        try:
            query = state["query"]
            # Deterministic mock behavior
            if self.is_mock:
                state["transport_modes"] = [
                    {"mode": "train", "from": query["from"], "to": query["to"], "date": query["date"], "priority": "high", "reasoning": "Mock: train primary"},
                    {"mode": "bus", "from": query["from"], "to": query["to"], "date": query["date"], "priority": "medium", "reasoning": "Mock: bus alternative"}
                ]
                state["current_step"] = "transport_selection_complete"
                state.setdefault("messages", []).append(HumanMessage(content=f"[MOCK] Select transport modes for {query['from']} to {query['to']}"))
                state["messages"].append(AIMessage(content=json.dumps(state["transport_modes"])))
                return state
            
            # Create the prompt
            messages = self.prompt.format_messages(
                from_location=query["from"],
                to_location=query["to"],
                date=query["date"],
                preferences=json.dumps(query.get("preferences", {}))
            )
            
            # Get LLM response
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            try:
                transport_modes = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to simple parsing if JSON fails
                transport_modes = [{
                    "mode": "train",
                    "from": query["from"],
                    "to": query["to"],
                    "date": query["date"],
                    "priority": "high",
                    "reasoning": "Fallback mode selection"
                }]
            
            # Update state
            state["transport_modes"] = transport_modes
            state["current_step"] = "transport_selection_complete"
            
            # Add to message history
            state["messages"].append(HumanMessage(content=f"Select transport modes for {query['from']} to {query['to']}"))
            state["messages"].append(AIMessage(content=response.content))
            
            return state
            
        except Exception as e:
            state["error"] = f"IngestAgent error: {str(e)}"
            return state

class LLMPlannerAgent:
    """LLM-powered agent for intelligent itinerary planning and optimization"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.is_mock = getattr(self.llm, "is_mock", False)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel itinerary planner for India. Your task is to create optimized travel itineraries by combining different transportation options.

Consider these factors when planning:
1. Logical sequence of travel segments
2. Reasonable transfer times between modes
3. Minimize total travel time and cost
4. Ensure practical connectivity
5. Account for Indian travel patterns and infrastructure

You will receive:
- Available flight options
- Available train options  
- Available bus options
- Available connector options (taxis, etc.)

Create 1-3 optimized itineraries by intelligently combining these options. Each itinerary should:
- Have a logical sequence of travel legs
- Include realistic transfer times
- Minimize unnecessary connections
- Consider cost vs time tradeoffs

Respond with a JSON array of itineraries:
[
  {
    "id": "itn-1",
    "legs": [list of selected travel legs in sequence],
    "total_estimated_time_min": total_time,
    "total_estimated_cost_inr": total_cost,
    "transfer_instructions": ["instruction1", "instruction2"],
    "notes": ["note1", "note2"],
    "optimization_strategy": "cost" | "time" | "balanced"
  }
]"""),
            ("human", """Plan optimized itineraries using these transportation options:

FLIGHT OPTIONS:
{flight_options}

TRAIN OPTIONS:
{train_options}

BUS OPTIONS:
{bus_options}

CONNECTOR OPTIONS:
{connector_options}

ORIGINAL QUERY:
From: {from_location}
To: {to_location}
Date: {date}
Preferences: {preferences}

Create 1-3 optimized itineraries considering cost, time, and convenience.""")
        ])
    
    def _get_realistic_route_data(self, from_city, to_city, date):
        """Get realistic route data based on actual Indian travel routes"""
        # Realistic route database with actual travel times and costs
        route_db = {
            ("New Delhi", "Mumbai"): {
                "flight": {"duration": 135, "price": 4500, "from": "Indira Gandhi International Airport (DEL)", "to": "Chhatrapati Shivaji International Airport (BOM)", "airline": "IndiGo", "flight_no": "6E-123"},
                "train": {"duration": 960, "price": 1800, "from": "New Delhi Railway Station (NDLS)", "to": "Mumbai Central (MMCT)", "train": "Rajdhani Express", "train_no": "12951"},
                "bus": {"duration": 1200, "price": 1200, "from": "New Delhi ISBT Kashmere Gate", "to": "Mumbai Central Bus Terminal", "operator": "State Transport", "type": "AC Sleeper"}
            },
            ("New Delhi", "Bangalore"): {
                "flight": {"duration": 165, "price": 5200, "from": "Indira Gandhi International Airport (DEL)", "to": "Kempegowda International Airport (BLR)", "airline": "SpiceJet", "flight_no": "SG-456"},
                "train": {"duration": 1800, "price": 2200, "from": "New Delhi Railway Station (NDLS)", "to": "Bangalore City Junction (SBC)", "train": "Karnataka Express", "train_no": "12627"},
                "bus": {"duration": 2160, "price": 1800, "from": "New Delhi ISBT Kashmere Gate", "to": "Bangalore Majestic Bus Stand", "operator": "Private Travels", "type": "Multi-Axle AC"}
            },
            ("Mumbai", "Pune"): {
                "train": {"duration": 210, "price": 250, "from": "Mumbai CST", "to": "Pune Junction", "train": "Deccan Express", "train_no": "11007"},
                "bus": {"duration": 180, "price": 300, "from": "Mumbai Central Bus Terminal", "to": "Pune Swargate Bus Stand", "operator": "MSRTC", "type": "AC Bus"}
            },
            ("New Delhi", "Chandigarh"): {
                "train": {"duration": 240, "price": 350, "from": "New Delhi Railway Station (NDLS)", "to": "Chandigarh Railway Station (CDG)", "train": "Shatabdi Express", "train_no": "12005"},
                "bus": {"duration": 300, "price": 400, "from": "New Delhi ISBT Kashmere Gate", "to": "Chandigarh ISBT Sector 43", "operator": "Haryana Roadways", "type": "AC Bus"}
            }
        }
        
        # Find matching route (check both directions)
        route_key = None
        for (city1, city2), data in route_db.items():
            if ((city1.lower() in from_city.lower() and city2.lower() in to_city.lower()) or
                (city2.lower() in from_city.lower() and city1.lower() in to_city.lower())):
                route_key = (city1, city2)
                break
        
        if not route_key:
            # Default fallback for unknown routes - clearly marked as demo
            return [{
                "mode": "train",
                "from": f"[DEMO] {from_city} Railway Station",
                "to": f"[DEMO] {to_city} Railway Station", 
                "dep_time": f"{date}T08:00:00+05:30",
                "arr_time": f"{date}T16:00:00+05:30",
                "duration_min": 480,
                "price_inr": 1200,
                "source": "demo_fallback",
                "train": "[DEMO] Express Train",
                "train_no": "[DEMO] 12345",
                "notes": "Demo data - actual route not in database"
            }]
        
        route_info = route_db[route_key]
        legs = []
        
        # Create realistic legs for each available mode
        for mode, info in route_info.items():
            if mode == "flight":
                legs.append({
                    "mode": "flight",
                    "from": info["from"],
                    "to": info["to"],
                    "dep_time": f"{date}T08:00:00+05:30",
                    "arr_time": f"{date}T{self._add_minutes_to_time_llm('08:00', info['duration'])}+05:30",
                    "duration_min": info["duration"],
                    "price_inr": info["price"],
                    "source": "realistic_demo",
                    "airline": info["airline"],
                    "flight_number": info["flight_no"]
                })
            elif mode == "train":
                legs.append({
                    "mode": "train",
                    "from": info["from"],
                    "to": info["to"],
                    "dep_time": f"{date}T14:00:00+05:30",
                    "arr_time": f"{date}T{self._add_minutes_to_time_llm('14:00', info['duration'])}+05:30",
                    "duration_min": info["duration"],
                    "price_inr": info["price"],
                    "source": "realistic_demo",
                    "train_name": info["train"],
                    "train_number": info["train_no"]
                })
            elif mode == "bus":
                legs.append({
                    "mode": "bus",
                    "from": info["from"],
                    "to": info["to"],
                    "dep_time": f"{date}T22:00:00+05:30",
                    "arr_time": f"{date}T{self._add_minutes_to_time_llm('22:00', info['duration'])}+05:30",
                    "duration_min": info["duration"],
                    "price_inr": info["price"],
                    "source": "realistic_demo",
                    "operator": info["operator"],
                    "bus_type": info["type"]
                })
        
        return legs
    
    def _add_minutes_to_time_llm(self, time_str, minutes):
        """Add minutes to time and return formatted time"""
        from datetime import datetime, timedelta
        time_obj = datetime.strptime(time_str, "%H:%M")
        new_time = time_obj + timedelta(minutes=minutes)
        # Handle day overflow
        if new_time.day > time_obj.day:
            return f"+1day {new_time.strftime('%H:%M')}"
        return new_time.strftime("%H:%M")
    
    def run(self, state: TravelPlanState) -> TravelPlanState:
        """Create optimized itineraries from available transportation options"""
        try:
            query = state["query"]
            # Deterministic mock behavior: build multiple realistic itineraries
            if self.is_mock:
                all_legs = (state.get("flight_options", []) + state.get("train_options", []) + state.get("bus_options", []) + state.get("connector_options", []))
                
                # If no options, create realistic mock legs based on query
                if not all_legs:
                    from_city = query["from"].split(",")[0].strip()
                    to_city = query["to"].split(",")[0].strip()
                    
                    # Get realistic data for the route
                    route_data = self._get_realistic_route_data(from_city, to_city, query['date'])
                    
                    all_legs = route_data
                
                # Create multiple itineraries with different strategies
                itineraries = []
                
                # Flight itinerary (fastest)
                flight_legs = [leg for leg in all_legs if leg.get("mode") == "flight"]
                if flight_legs:
                    flight_leg = flight_legs[0]
                    itineraries.append({
                        "id": "itn-mock-flight",
                        "legs": [flight_leg],
                        "total_estimated_time_min": flight_leg.get("duration_min", 150),
                        "total_estimated_cost_inr": flight_leg.get("price_inr", 4500),
                        "transfer_instructions": [],
                        "notes": ["[MOCK] Direct flight - fastest option"],
                        "optimization_strategy": "time"
                    })
                
                # Train itinerary (balanced)
                train_legs = [leg for leg in all_legs if leg.get("mode") == "train"]
                if train_legs:
                    train_leg = train_legs[0]
                    itineraries.append({
                        "id": "itn-mock-train",
                        "legs": [train_leg],
                        "total_estimated_time_min": train_leg.get("duration_min", 480),
                        "total_estimated_cost_inr": train_leg.get("price_inr", 1200),
                        "transfer_instructions": [],
                        "notes": ["[MOCK] Direct train - comfortable journey"],
                        "optimization_strategy": "balanced"
                    })
                
                # Bus itinerary (cheapest)
                bus_legs = [leg for leg in all_legs if leg.get("mode") == "bus"]
                if bus_legs:
                    bus_leg = bus_legs[0]
                    itineraries.append({
                        "id": "itn-mock-bus",
                        "legs": [bus_leg],
                        "total_estimated_time_min": bus_leg.get("duration_min", 480),
                        "total_estimated_cost_inr": bus_leg.get("price_inr", 800),
                        "transfer_instructions": [],
                        "notes": ["[MOCK] Direct bus - most economical"],
                        "optimization_strategy": "cost"
                    })
                
                # Ensure at least one itinerary
                if not itineraries:
                    itineraries = [{
                        "id": "itn-mock-fallback",
                        "legs": all_legs[:1],
                        "total_estimated_time_min": 360,
                        "total_estimated_cost_inr": 1000,
                        "transfer_instructions": [],
                        "notes": ["[MOCK] Fallback option"],
                        "optimization_strategy": "balanced"
                    }]
                
                state["itineraries"] = itineraries
                state["current_step"] = "itinerary_planning_complete"
                state.setdefault("messages", []).append(HumanMessage(content="[MOCK] Plan optimized itineraries"))
                state["messages"].append(AIMessage(content=json.dumps(itineraries)))
                return state
            
            # Format transportation options for the prompt
            flight_options = json.dumps(state.get("flight_options", []), indent=2)
            train_options = json.dumps(state.get("train_options", []), indent=2)
            bus_options = json.dumps(state.get("bus_options", []), indent=2)
            connector_options = json.dumps(state.get("connector_options", []), indent=2)
            
            # Create the prompt
            messages = self.prompt.format_messages(
                flight_options=flight_options,
                train_options=train_options,
                bus_options=bus_options,
                connector_options=connector_options,
                from_location=query["from"],
                to_location=query["to"],
                date=query["date"],
                preferences=json.dumps(query.get("preferences", {}))
            )
            
            # Get LLM response
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            try:
                itineraries = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback itinerary if JSON parsing fails
                all_legs = (state.get("flight_options", []) + 
                           state.get("train_options", []) + 
                           state.get("bus_options", []) + 
                           state.get("connector_options", []))
                
                if all_legs:
                    total_time = sum(leg.get("duration_min", 0) for leg in all_legs)
                    total_cost = sum(leg.get("price_inr", 0) for leg in all_legs)
                    
                    itineraries = [{
                        "id": "itn-fallback",
                        "legs": all_legs,
                        "total_estimated_time_min": total_time,
                        "total_estimated_cost_inr": total_cost,
                        "transfer_instructions": ["Fallback itinerary - check connections"],
                        "notes": ["Generated automatically due to parsing error"],
                        "optimization_strategy": "fallback"
                    }]
                else:
                    itineraries = []
            
            # Update state
            state["itineraries"] = itineraries
            state["current_step"] = "itinerary_planning_complete"
            
            # Add to message history
            state["messages"].append(HumanMessage(content="Plan optimized itineraries from available options"))
            state["messages"].append(AIMessage(content=response.content))
            
            return state
            
        except Exception as e:
            state["error"] = f"PlannerAgent error: {str(e)}"
            return state

class LLMRankingAgent:
    """LLM-powered agent for intelligent itinerary ranking based on user preferences"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm = llm_config.get_llm()
        self.is_mock = getattr(self.llm, "is_mock", False)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel advisor specializing in ranking travel itineraries based on user preferences.

Your task is to analyze and score itineraries considering:
1. User preferences (cost, time, comfort, convenience)
2. Practical factors (transfer complexity, reliability)
3. Indian travel context (infrastructure, seasonal factors)
4. Overall travel experience quality

Scoring criteria (0.0 to 1.0):
- Cost Score: Lower cost = higher score
- Time Score: Shorter time = higher score  
- Comfort Score: Fewer transfers, better modes = higher score
- Convenience Score: Practical departure times, good connections = higher score

For each itinerary, provide:
- Individual scores for each criterion
- Overall weighted score based on user preferences
- Ranking explanation
- Recommendations for improvement

Respond with the itineraries in ranked order (best first) with added scoring:
[
  {
    ...original_itinerary_data...,
    "score": {
      "cost": 0.85,
      "time": 0.72,
      "comfort": 0.90,
      "convenience": 0.78,
      "overall": 0.81
    },
    "rank": 1,
    "ranking_explanation": "Best overall value with good balance of cost and comfort",
    "recommendations": ["Consider booking in advance for better prices"]
  }
]"""),
            ("human", """Rank these itineraries based on user preferences:

ITINERARIES:
{itineraries}

USER PREFERENCES:
{preferences}

RANKING CRITERIA:
- Prioritize: {prioritize}
- Budget considerations: {budget_notes}
- Time constraints: {time_notes}

Rank from best to worst and provide detailed scoring.""")
        ])
    
    def run(self, state: TravelPlanState) -> TravelPlanState:
        """Rank itineraries based on user preferences and travel factors"""
        try:
            query = state["query"]
            itineraries = state.get("itineraries", [])
            
            if not itineraries:
                state["ranked_itineraries"] = []
                return state
            
            # Deterministic mock behavior
            if self.is_mock:
                preferences = query.get("preferences", {})
                prioritize = preferences.get("prioritize", "balanced")
                
                ranked_itineraries = []
                for i, itin in enumerate(itineraries):
                    cost = itin.get("total_estimated_cost_inr", 0)
                    time = itin.get("total_estimated_time_min", 1)
                    strategy = itin.get("optimization_strategy", "balanced")
                    
                    # Calculate scores based on strategy
                    cost_score = max(0.0, min(1.0, 1.0 - (cost / 10000.0)))
                    time_score = max(0.0, min(1.0, 1.0 - (time / 2000.0)))
                    
                    # Adjust comfort and convenience based on mode
                    legs = itin.get("legs", [])
                    if legs:
                        primary_mode = legs[0].get("mode", "bus")
                        if primary_mode == "flight":
                            comfort_score = 0.9
                            convenience_score = 0.8
                        elif primary_mode == "train":
                            comfort_score = 0.8
                            convenience_score = 0.7
                        else:  # bus
                            comfort_score = 0.6
                            convenience_score = 0.6
                    else:
                        comfort_score = 0.7
                        convenience_score = 0.6
                    
                    # Weight scores based on user preference
                    if prioritize == "cost":
                        overall = 0.5 * cost_score + 0.2 * time_score + 0.2 * comfort_score + 0.1 * convenience_score
                        explanation = f"[MOCK] Ranked high for cost efficiency (₹{cost})"
                    elif prioritize == "time":
                        overall = 0.2 * cost_score + 0.5 * time_score + 0.2 * comfort_score + 0.1 * convenience_score
                        explanation = f"[MOCK] Ranked for speed ({time//60}h {time%60}m total)"
                    else:  # balanced
                        overall = 0.3 * cost_score + 0.3 * time_score + 0.2 * comfort_score + 0.2 * convenience_score
                        explanation = f"[MOCK] Balanced option considering cost (₹{cost}) and time ({time//60}h {time%60}m)"
                    
                    # Generate recommendations based on strategy
                    recommendations = []
                    if strategy == "cost":
                        recommendations.append("[MOCK] Most economical option - book early for better deals")
                    elif strategy == "time":
                        recommendations.append("[MOCK] Fastest option - check for delays during peak season")
                    else:
                        recommendations.append("[MOCK] Good balance of cost and time - reliable choice")
                    
                    if len(legs) > 1:
                        recommendations.append("[MOCK] Multiple transfers - allow extra time for connections")
                    
                    itin_copy = itin.copy()
                    itin_copy["score"] = {
                        "cost": round(cost_score, 2),
                        "time": round(time_score, 2),
                        "comfort": round(comfort_score, 2),
                        "convenience": round(convenience_score, 2),
                        "overall": round(overall, 2)
                    }
                    itin_copy["ranking_explanation"] = explanation
                    itin_copy["recommendations"] = recommendations
                    ranked_itineraries.append(itin_copy)
                
                # Sort by overall score (highest first)
                ranked_itineraries.sort(key=lambda x: x["score"]["overall"], reverse=True)
                
                # Add ranks
                for i, itin in enumerate(ranked_itineraries):
                    itin["rank"] = i + 1
                
                state["ranked_itineraries"] = ranked_itineraries
                state["current_step"] = "ranking_complete"
                state.setdefault("messages", []).append(HumanMessage(content="[MOCK] Rank itineraries"))
                state["messages"].append(AIMessage(content=json.dumps(ranked_itineraries)))
                return state
            
            preferences = query.get("preferences", {})
            prioritize = preferences.get("prioritize", "balanced")
            
            # Create budget and time notes based on preferences
            budget_notes = "Cost-conscious" if prioritize == "cost" else "Flexible budget"
            time_notes = "Time-sensitive" if prioritize == "time" else "Flexible schedule"
            
            # Create the prompt
            messages = self.prompt.format_messages(
                itineraries=json.dumps(itineraries, indent=2),
                preferences=json.dumps(preferences),
                prioritize=prioritize,
                budget_notes=budget_notes,
                time_notes=time_notes
            )
            
            # Get LLM response
            response = self.llm.invoke(messages)
            
            # Parse the JSON response
            try:
                ranked_itineraries = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback ranking using simple heuristics
                ranked_itineraries = []
                for i, itin in enumerate(itineraries):
                    cost = itin.get("total_estimated_cost_inr", 0)
                    time = itin.get("total_estimated_time_min", 1)
                    
                    # Simple scoring
                    cost_score = max(0.0, min(1.0, 1.0 - (cost / 10000.0)))
                    time_score = max(0.0, min(1.0, 1.0 - (time / 2000.0)))
                    comfort_score = 0.7  # Default
                    convenience_score = 0.6  # Default
                    
                    if prioritize == "cost":
                        overall = 0.5 * cost_score + 0.2 * time_score + 0.2 * comfort_score + 0.1 * convenience_score
                    elif prioritize == "time":
                        overall = 0.2 * cost_score + 0.5 * time_score + 0.2 * comfort_score + 0.1 * convenience_score
                    else:
                        overall = 0.3 * cost_score + 0.3 * time_score + 0.2 * comfort_score + 0.2 * convenience_score
                    
                    itin_copy = itin.copy()
                    itin_copy["score"] = {
                        "cost": round(cost_score, 2),
                        "time": round(time_score, 2),
                        "comfort": round(comfort_score, 2),
                        "convenience": round(convenience_score, 2),
                        "overall": round(overall, 2)
                    }
                    itin_copy["rank"] = i + 1
                    itin_copy["ranking_explanation"] = "Fallback ranking based on simple heuristics"
                    itin_copy["recommendations"] = ["Check availability and book in advance"]
                    
                    ranked_itineraries.append(itin_copy)
                
                # Sort by overall score
                ranked_itineraries.sort(key=lambda x: x["score"]["overall"], reverse=True)
                
                # Update ranks
                for i, itin in enumerate(ranked_itineraries):
                    itin["rank"] = i + 1
            
            # Update state
            state["ranked_itineraries"] = ranked_itineraries
            state["current_step"] = "ranking_complete"
            
            # Add to message history
            state["messages"].append(HumanMessage(content="Rank itineraries based on preferences"))
            state["messages"].append(AIMessage(content=response.content))
            
            return state
            
        except Exception as e:
            state["error"] = f"RankingAgent error: {str(e)}"
            return state

class TravelPlannerWorkflow:
    """LangGraph workflow orchestrating the multi-agent travel planning system"""
    
    def __init__(self):
        self.llm_config = LLMConfig()
        self.ingest_agent = LLMIngestAgent(self.llm_config)
        self.planner_agent = LLMPlannerAgent(self.llm_config)
        self.ranking_agent = LLMRankingAgent(self.llm_config)
        
        # Import the existing transport agents
        from agents import FlightAgent, TrainAgent, BusAgent, ConnectorAgent
        self.flight_agent = FlightAgent(mode="hybrid")  # Use hybrid mode for real data
        self.train_agent = TrainAgent(mode="hybrid")
        self.bus_agent = BusAgent(mode="hybrid")
        self.connector_agent = ConnectorAgent(mode="static")
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(TravelPlanState)
        
        # Add nodes for each agent
        workflow.add_node("ingest", self._ingest_node)
        workflow.add_node("fetch_transport", self._fetch_transport_node)
        workflow.add_node("plan_itineraries", self._plan_itineraries_node)
        workflow.add_node("rank_itineraries", self._rank_itineraries_node)
        
        # Define the workflow edges
        workflow.set_entry_point("ingest")
        workflow.add_edge("ingest", "fetch_transport")
        workflow.add_edge("fetch_transport", "plan_itineraries")
        workflow.add_edge("plan_itineraries", "rank_itineraries")
        workflow.add_edge("rank_itineraries", END)
        
        return workflow.compile()
    
    def _ingest_node(self, state: TravelPlanState) -> TravelPlanState:
        """Node for LLM-powered transport mode selection"""
        return self.ingest_agent.run(state)
    
    def _fetch_transport_node(self, state: TravelPlanState) -> TravelPlanState:
        """Node for fetching transportation options from existing agents"""
        try:
            transport_modes = state.get("transport_modes", [])
            
            # Initialize option lists
            state["flight_options"] = []
            state["train_options"] = []
            state["bus_options"] = []
            state["connector_options"] = []
            
            # Fetch options for each requested transport mode
            for mode_request in transport_modes:
                mode = mode_request.get("mode")
                
                if mode == "flight":
                    options = self.flight_agent.run(mode_request)
                    state["flight_options"].extend(options)
                elif mode == "train":
                    options = self.train_agent.run(mode_request)
                    state["train_options"].extend(options)
                elif mode == "bus":
                    options = self.bus_agent.run(mode_request)
                    state["bus_options"].extend(options)
            
            # Generate connector options if we have multiple transport modes
            all_legs = (state["flight_options"] + state["train_options"] + state["bus_options"])
            if len(all_legs) > 1:
                connectors = self.connector_agent.run(all_legs)
                state["connector_options"] = connectors
            
            state["current_step"] = "transport_fetch_complete"
            return state
            
        except Exception as e:
            state["error"] = f"Transport fetch error: {str(e)}"
            return state
    
    def _plan_itineraries_node(self, state: TravelPlanState) -> TravelPlanState:
        """Node for LLM-powered itinerary planning"""
        return self.planner_agent.run(state)
    
    def _rank_itineraries_node(self, state: TravelPlanState) -> TravelPlanState:
        """Node for LLM-powered itinerary ranking"""
        return self.ranking_agent.run(state)
    
    def run_planning_workflow(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete travel planning workflow"""
        
        # Initialize state
        initial_state = TravelPlanState(
            query=query,
            messages=[],
            transport_modes=[],
            flight_options=[],
            train_options=[],
            bus_options=[],
            connector_options=[],
            itineraries=[],
            ranked_itineraries=[],
            current_step="initialized",
            error=None
        )
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Check for errors
            if final_state.get("error"):
                return {
                    "query": query,
                    "error": final_state["error"],
                    "itineraries": [],
                    "sources": [{"name": "langgraph_workflow", "url": "local", "access": "llm"}]
                }
            
            # Add comprehensive disclaimers for LLM mode - LLM + HYBRID DATA
            data_disclaimer = {
                "data_type": "LLM_WITH_HYBRID_DATA",
                "disclaimer": "🧠 LLM MODE: AI-powered planning with REAL DATA from free APIs + intelligent fallbacks.",
                "llm_features": {
                    "intelligence": "AI-powered route optimization (working)",
                    "reasoning": "Contextual analysis of preferences (working)",
                    "recommendations": "Personalized suggestions (working)",
                    "workflow": "LangGraph multi-agent orchestration (working)"
                },
                "data_sources": {
                    "flights": "OpenSky Network (live) + LLM planning → demo fallback",
                    "trains": "Railway MCP (live) + LLM planning → demo fallback",
                    "buses": "Regional APIs + LLM planning → demo fallback",
                    "planning": "LangGraph workflow with IngestAgent, PlannerAgent, RankingAgent"
                },
                "real_data_coverage": {
                    "trains": "Live data for major routes via Railway MCP",
                    "flights": "Live aircraft tracking via OpenSky Network",
                    "buses": "Regional coverage (Delhi, Bangalore)",
                    "ai_planning": "Full LLM-powered optimization and ranking"
                },
                "limitations": {
                    "booking": "Planning only - cannot make actual reservations",
                    "coverage": "Real data limited by free API quotas and regional coverage",
                    "accuracy": "Real data subject to API availability and rate limits"
                },
                "best_of_both": "Combines REAL live data with AI-powered intelligent planning",
                "api_status": "Check console logs to see which APIs provided real vs demo data",
                "mock_mode": not self.llm_config.has_real_llm_config()
            }
            
            # Format the response
            result = {
                "query": query,
                "itineraries": final_state.get("ranked_itineraries", []),
                "sources": [
                    {"name": "langgraph_workflow", "url": "local", "access": "llm"},
                    {"name": "llm_agents", "url": "openai/anthropic", "access": "api"}
                ],
                "workflow_steps": final_state.get("current_step", "unknown"),
                "transport_analysis": final_state.get("transport_modes", []),
                "data_disclaimer": data_disclaimer
            }
            
            return result
            
        except Exception as e:
            return {
                "query": query,
                "error": f"Workflow execution error: {str(e)}",
                "itineraries": [],
                "sources": [{"name": "langgraph_workflow", "url": "local", "access": "llm"}]
            }

# Global workflow instance
_workflow_instance = None

def get_workflow() -> TravelPlannerWorkflow:
    """Get or create the global workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = TravelPlannerWorkflow()
    return _workflow_instance
