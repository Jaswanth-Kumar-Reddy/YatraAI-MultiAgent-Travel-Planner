# LangGraph/LLM Integration Guide

## 🚀 Overview

This document explains the comprehensive LangGraph/LLM integration that transforms your multi-agent travel planner from simple rule-based logic to intelligent LLM-powered agents.

## 🏗️ Architecture

### LangGraph Workflow
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│ IngestAgent │───▶│ FetchTransport│───▶│PlannerAgent │───▶│RankingAgent │
│   (LLM)     │    │   (Existing)  │    │   (LLM)     │    │   (LLM)     │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

### State Management
The workflow uses a shared `TravelPlanState` that flows between agents:
- **Input**: User query with preferences
- **Transport Analysis**: LLM-selected transport modes
- **Options**: Flight/train/bus/connector options
- **Itineraries**: LLM-optimized travel plans
- **Ranking**: LLM-scored and ranked results

## 🧠 LLM-Powered Agents

### 1. LLMIngestAgent
**Purpose**: Intelligent transportation mode selection

**LLM Prompt**: Analyzes travel query considering:
- Distance between locations
- Available transport in India
- User preferences (cost/time/comfort)
- Practical connectivity

**Output**: JSON array of transport mode requests with priorities and reasoning

**Example**:
```json
[
  {
    "mode": "train",
    "from": "New Delhi, Delhi, India",
    "to": "Mumbai, Maharashtra, India",
    "date": "2025-01-15",
    "priority": "high",
    "reasoning": "Long distance route with excellent train connectivity"
  }
]
```

### 2. LLMPlannerAgent
**Purpose**: Intelligent itinerary optimization

**LLM Prompt**: Creates optimized itineraries by:
- Combining transport options logically
- Minimizing transfer times
- Balancing cost vs time
- Ensuring practical connectivity

**Output**: 1-3 optimized itineraries with different strategies

**Example**:
```json
[
  {
    "id": "itn-1",
    "legs": [...],
    "total_estimated_time_min": 720,
    "total_estimated_cost_inr": 2500,
    "optimization_strategy": "balanced"
  }
]
```

### 3. LLMRankingAgent
**Purpose**: Preference-based intelligent ranking

**LLM Prompt**: Scores itineraries considering:
- User preferences (cost/time/comfort priority)
- Practical factors (transfer complexity)
- Indian travel context
- Overall experience quality

**Output**: Ranked itineraries with detailed scoring

**Example**:
```json
[
  {
    "score": {
      "cost": 0.85,
      "time": 0.72,
      "comfort": 0.90,
      "overall": 0.81
    },
    "rank": 1,
    "ranking_explanation": "Best overall value with good balance"
  }
]
```

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure:

```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # or 'anthropic'

# OpenAI (recommended)
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini

# Or Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Usage Modes

#### Auto Mode (Recommended)
```python
query = {
    'from': 'New Delhi, Delhi, India',
    'to': 'Mumbai, Maharashtra, India',
    'date': '2025-01-15',
    'mode': 'auto'  # Auto-detects LLM availability
}
```

#### Explicit LLM Mode
```python
query = {
    'from': 'New Delhi, Delhi, India',
    'to': 'Mumbai, Maharashtra, India',
    'date': '2025-01-15',
    'mode': 'llm'  # Force LLM mode
}
```

#### Traditional Mode (Fallback)
```python
query = {
    'from': 'New Delhi, Delhi, India',
    'to': 'Mumbai, Maharashtra, India',
    'date': '2025-01-15',
    'mode': 'api'  # Use rule-based agents
}
```

## 🌐 Frontend Integration

The web interface now supports LLM mode selection:

- **🤖 Auto**: Automatically uses LLM if API keys are available
- **🧠 LLM Agents**: Force LLM-powered planning
- **🔗 Real APIs**: Traditional rule-based agents
- **📊 Demo Data**: Static demo data

## 🔄 Workflow Execution

### Step 1: Transport Mode Selection
```python
# LLM analyzes: "Delhi to Mumbai on 2025-01-15"
# Output: [{"mode": "train", "priority": "high", "reasoning": "..."}]
```

### Step 2: Fetch Transport Options
```python
# Uses existing agents to get real data
# flight_options = FlightAgent().run(...)
# train_options = TrainAgent().run(...)
```

### Step 3: Itinerary Planning
```python
# LLM creates optimized combinations
# Output: Multiple itineraries with different strategies
```

### Step 4: Intelligent Ranking
```python
# LLM scores based on user preferences
# Output: Ranked itineraries with explanations
```

## 🎯 Key Benefits

### 1. **Intelligent Decision Making**
- LLM considers context, not just rules
- Adapts to user preferences dynamically
- Provides reasoning for decisions

### 2. **Better User Experience**
- Natural language understanding
- Personalized recommendations
- Detailed explanations

### 3. **Flexible Architecture**
- Seamless fallback to traditional agents
- Easy to extend with new LLM providers
- Maintains existing API integrations

### 4. **Production Ready**
- Error handling and fallbacks
- Environment-based configuration
- Scalable state management

## 🧪 Testing

### Test LLM Integration
```bash
# Set your API key
export OPENAI_API_KEY="your_key_here"

# Run with LLM mode
python planner.py --from "New Delhi" --to "Mumbai" --date "2025-01-15" --mode llm
```

### Test Fallback
```bash
# Without API key - should fallback to traditional agents
python planner.py --from "New Delhi" --to "Mumbai" --date "2025-01-15" --mode api
```

### Web Interface Test
```bash
# Start the server
python app.py

# Visit http://localhost:5000
# Select "🧠 LLM Agents" mode and test
```

## 🔮 Advanced Features

### Custom LLM Models
```python
# In .env file
LLM_MODEL=gpt-4  # Use GPT-4 for better reasoning
LLM_MODEL=gpt-3.5-turbo  # Use GPT-3.5 for faster responses
```

### Anthropic Claude
```python
# In .env file
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
```

### Debug Mode
```python
# In .env file
DEBUG_MODE=true  # Enable detailed logging
```

## 🚨 Error Handling

The system includes comprehensive error handling:

1. **Missing API Keys**: Falls back to traditional agents
2. **LLM API Errors**: Returns error message with fallback
3. **JSON Parsing Errors**: Uses heuristic fallbacks
4. **Network Issues**: Graceful degradation

## 📊 Performance Considerations

### LLM Response Times
- **GPT-4o-mini**: ~2-5 seconds per agent
- **GPT-3.5-turbo**: ~1-3 seconds per agent
- **Claude-3.5-sonnet**: ~2-4 seconds per agent

### Cost Optimization
- Uses efficient models (GPT-4o-mini recommended)
- Structured prompts minimize token usage
- Fallback prevents unnecessary API calls

## 🔧 Troubleshooting

### Common Issues

1. **"LangGraph dependencies not installed"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"No LLM API key configured"**
   ```bash
   export OPENAI_API_KEY="your_key_here"
   ```

3. **"LLM workflow error"**
   - Check API key validity
   - Verify internet connection
   - Check API rate limits

### Debug Tips
```python
# Enable debug mode
export DEBUG_MODE=true

# Check configuration
python -c "from langgraph_workflow import LLMConfig; print(LLMConfig().__dict__)"
```

## 🎉 Success Metrics

After integration, you should see:

✅ **Intelligent Mode Selection**: LLM chooses optimal transport modes  
✅ **Contextual Planning**: Considers user preferences and constraints  
✅ **Detailed Explanations**: Reasoning for each decision  
✅ **Flexible Ranking**: Adapts to different priority preferences  
✅ **Seamless Fallback**: Works even without LLM configuration  

Your Multi-Agent Travel Planner is now powered by state-of-the-art LLM intelligence! 🚀
