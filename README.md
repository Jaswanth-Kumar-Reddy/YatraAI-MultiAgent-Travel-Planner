# 🚀 YatraAI - Smart Yatra Planning with AI


A sophisticated Multi-Agent AI travel planning system using **LangGraph**, **LLM integration**, and **real-time data** from free community APIs. Experience the future of intelligent yatra planning!

### ✅ **Live Data Sources (Working Now!)**
- **🛩️ Flights**: OpenSky Network (live aircraft tracking - FREE)
- **🚂 Trains**: Railway MCP Server (live Indian Railways - FREE)  
- **🚌 Buses**: Regional APIs (Delhi DTC, Bangalore BMTC - FREE)
- **🤖 AI Planning**: LangGraph multi-agent workflow with LLM integration

### ✅ **Multi-Agent Architecture**
- **LangGraph Workflow**: Orchestrates 3 LLM-powered agents
- **IngestAgent**: Intelligent transport mode selection
- **PlannerAgent**: Optimized itinerary creation with preference balancing
- **RankingAgent**: AI-powered scoring with detailed explanations
- **Hybrid Data**: Real APIs with intelligent demo fallbacks

## 🏃‍♂️ Quick Start

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Start the Server**
```bash
python3 app.py
```

### **3. Test YatraAI (No API Keys Needed!)**
```bash
# Test hybrid mode with real data
curl -X POST http://127.0.0.1:5002/api/plan \
  -H "Content-Type: application/json" \
  -d '{"from":"New Delhi","to":"Mumbai","date":"2025-10-01","mode":"hybrid"}'
```

### **4. Optional: Add Free API Keys**
```bash
# Copy environment template
cp .env.hybrid.example .env

# Edit .env and add your free API keys:
# VARIFLIGHT_KEY=your_variflight_key      # 100 free calls
# SERPAPI_KEY=your_serpapi_key            # 100 free searches  
# AVIATIONSTACK_KEY=your_aviationstack_key # 1000 free requests
# OPENAI_API_KEY=your_openai_key          # For LLM mode
# ANTHROPIC_API_KEY=your_anthropic_key    # For LLM mode
```

## 🎯 **Available Modes**

| Mode | Description | Data Sources | Use Case |
|------|-------------|--------------|----------|
| `hybrid` | **🔄 Real Data** - Free APIs + Demo fallback | OpenSky + Railway MCP + Regional | **Best for real data demo** |
| `static` | **📊 Demo** - Realistic demo data only | Static demo data | Offline demo/portfolio |
| `llm` | **🧠 AI + Real Data** - LLM + Hybrid data | **Real APIs + AI planning** | **🏆 BEST EXPERIENCE** |
| `api` | **🔌 API** - Traditional API calls | API endpoints + fallbacks | API integration demo |
| `auto` | **🤖 Smart** - LLM if keys, else Hybrid | **Auto: LLM+Real or Real only** | **Recommended for users** |

## 🌐 **Frontend Interface**

### **Web Interface**
Visit: `http://localhost:5002` for the interactive web interface

### **API Endpoint**  
```bash
POST http://localhost:5002/api/plan
Content-Type: application/json

{
  "from": "New Delhi, Delhi, India",
  "to": "Mumbai, Maharashtra, India", 
  "date": "2025-10-01",
  "mode": "hybrid",
  "preferences": {"prioritize": "cost"}
}
```

## 📊 **Real Data Examples**

### **✅ Live Flight Data (OpenSky Network)**
```json
{
  "flight_number": "AIC2486",
  "airline": "India",
  "source": "opensky_live",
  "availability": "Live aircraft tracking data"
}
```

### **✅ Live Train Data (Railway MCP)**
```json
{
  "train_number": "12472",
  "train_name": "SWARAJ EXPRESS",
  "source": "railway_mcp_live",
  "availability": "Live from Railway MCP"
}
```

## 🏗️ **Architecture Overview**

### **Multi-Agent System**
```
User Query → Hybrid Agents → Real APIs (try) → Demo Fallback
                ↓
        LangGraph Workflow (LLM Agents)
                ↓
        AI-Powered Planning & Ranking
                ↓
        Optimized Itineraries with Transparency
```

### **Key Components**
- **🔄 Hybrid Agents**: `hybrid_agents.py` - Real API integration
- **🤖 LangGraph Workflow**: `langgraph_workflow.py` - AI orchestration  
- **🧠 LLM Agents**: IngestAgent, PlannerAgent, RankingAgent
- **📊 Traditional Agents**: `agents.py` - Rule-based fallbacks
- **🌐 Flask API**: `app.py` - RESTful interface
- **💾 Data Sources**: Free community APIs + intelligent fallbacks

## 🎉 **Success Metrics**

### **✅ Real Data Integration**
- **Flights**: OpenSky Network (100% free, global coverage)
- **Trains**: Railway MCP (100% free, Indian Railways)
- **Buses**: Regional APIs (Delhi, Bangalore coverage)

### **✅ Console Verification**
```
✅ Got 5 flights from OpenSky Network    # Real flight data
✅ Got 5 trains from Railway MCP         # Real train data
✅ Got 2 buses from Delhi DTC            # Regional data
```

### **✅ API Response Verification**
```bash
# Check data sources in response
curl -s http://localhost:5002/api/plan -d '{"mode":"hybrid"}' | \
  jq '.itineraries[].legs[].source'

# Output:
# "opensky_live"      ← Real flight data
# "railway_mcp_live"  ← Real train data
```

## 📚 **Documentation**

- **📋 [REAL_DATA_SUCCESS.md](REAL_DATA_SUCCESS.md)** - Complete success summary
- **🔧 [HYBRID_SETUP_GUIDE.md](HYBRID_SETUP_GUIDE.md)** - Detailed setup instructions
- **🌐 [FREE_API_SOURCES.md](FREE_API_SOURCES.md)** - API research and sources
- **🤖 [LANGGRAPH_INTEGRATION.md](LANGGRAPH_INTEGRATION.md)** - LLM integration details
- **🔌 [REAL_TIME_API_INTEGRATION.md](REAL_TIME_API_INTEGRATION.md)** - API integration guide

## 🚀 **Perfect For**

### **Portfolio Demonstrations**
- ✅ Real API integration skills
- ✅ Multi-agent system design
- ✅ LangGraph/LLM architecture
- ✅ Error handling & fallbacks
- ✅ Production-ready patterns

### **Technical Interviews**
- ✅ System design expertise
- ✅ API integration patterns
- ✅ AI/ML implementation
- ✅ Scalable architecture
- ✅ Real-world problem solving

### **Client Presentations**
- ✅ Live data capabilities
- ✅ Professional UI/UX
- ✅ Transparent operation
- ✅ Intelligent fallbacks
- ✅ Cost-effective solutions

## 🎯 **Future Enhancements**

### **Ready to Scale**
- **🔑 Premium APIs**: Easy upgrade to Amadeus, IRCTC partnerships
- **💳 Booking Integration**: Payment gateway integration ready
- **🌍 Global Coverage**: Expand to international routes
- **📱 Mobile App**: React Native/Flutter implementation
- **🔄 Real-Time Updates**: WebSocket integration for live updates

### **AI Enhancements**
- **🧠 Advanced LLM**: GPT-4, Claude-3 integration
- **📊 Predictive Analytics**: Price prediction, delay forecasting
- **🎯 Personalization**: User preference learning
- **🗣️ Voice Interface**: Speech-to-text integration
- **📸 Visual Search**: Image-based destination search

## 🏆 **Achievement Summary**

### **✅ MISSION ACCOMPLISHED**
- **Real-time data integration** using free community APIs ✅
- **Multi-agent AI architecture** with LangGraph/LLM ✅
- **Production-ready patterns** with robust error handling ✅
- **Transparent operation** with clear data attribution ✅
- **Zero-cost demonstration** capabilities ✅
- **Scalable design** ready for production upgrades ✅

**YatraAI is now a sophisticated, real-time system perfect for demonstrations, portfolios, and technical showcases!** 🎉

---

*YatraAI - Built with ❤️ using LangGraph, OpenAI/Anthropic LLMs, OpenSky Network, Railway MCP, and community APIs*

