#!/usr/bin/env python3
"""
Test script for LangGraph/LLM integration in Multi-Agent Travel Planner
"""

import os
import json
import sys
from datetime import datetime, timedelta

def test_environment_setup():
    """Test if environment or mock LLM is available"""
    print("🔧 Testing Environment Setup...")
    
    # Prefer real keys if present
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if openai_key:
        print("✅ OpenAI API key found")
        return True
    if anthropic_key:
        print("✅ Anthropic API key found")
        return True
    
    # Otherwise verify mock LLM is available through config
    try:
        from langgraph_workflow import LLMConfig
        llm = LLMConfig().get_llm()
        # If no exception raised, mock works
        print("✅ No API keys found; using Mock LLM for offline tests")
        return True
    except Exception as e:
        print("❌ No LLM available (neither API keys nor mock)")
        print(f"   Details: {e}")
        return False

def test_dependencies():
    """Test if required dependencies are installed"""
    print("\n📦 Testing Dependencies...")
    
    try:
        import langgraph
        print("✅ LangGraph installed")
    except ImportError:
        print("❌ LangGraph not installed")
        return False
    
    try:
        import langchain
        print("✅ LangChain installed")
    except ImportError:
        print("❌ LangChain not installed")
        return False
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ LangChain OpenAI integration available")
    except ImportError:
        print("⚠️  LangChain OpenAI integration not available")
    
    try:
        from langchain_anthropic import ChatAnthropic
        print("✅ LangChain Anthropic integration available")
    except ImportError:
        print("⚠️  LangChain Anthropic integration not available")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ LangChain Google Gemini integration available")
    except ImportError:
        print("⚠️  LangChain Google Gemini integration not available")
    
    return True

def test_workflow_import():
    """Test if LangGraph workflow can be imported"""
    print("\n🔄 Testing Workflow Import...")
    
    try:
        from langgraph_workflow import get_workflow, LLMConfig
        print("✅ LangGraph workflow imported successfully")
        
        # Test LLM configuration
        config = LLMConfig()
        print(f"✅ LLM Provider: {config.model_provider}")
        print(f"✅ LLM Model: {config.model_name}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import workflow: {str(e)}")
        return False

def test_llm_connection():
    """Test if LLM connection works"""
    print("\n🧠 Testing LLM Connection...")
    
    try:
        from langgraph_workflow import LLMConfig
        
        config = LLMConfig()
        llm = config.get_llm()
        
        # Test with a simple message
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Hello! Respond with just 'OK' if you can hear me.")])
        
        print(f"✅ LLM Response: {response.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ LLM connection failed: {str(e)}")
        return False

def test_traditional_mode():
    """Test traditional (non-LLM) mode still works"""
    print("\n🔗 Testing Traditional Mode...")
    
    try:
        from planner import run_traditional_query
        
        query = {
            'from': 'New Delhi, Delhi, India',
            'to': 'Mumbai, Maharashtra, India',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'preferences': {'prioritize': 'cost'}
        }
        
        result = run_traditional_query(query, mode='static')
        
        if result.get('itineraries'):
            print("✅ Traditional mode working")
            print(f"   Generated {len(result['itineraries'])} itinerary(ies)")
            return True
        else:
            print("❌ Traditional mode failed - no itineraries generated")
            return False
            
    except Exception as e:
        print(f"❌ Traditional mode failed: {str(e)}")
        return False

def test_llm_mode():
    """Test LLM mode, using Mock LLM if no API keys"""
    print("\n🤖 Testing LLM Mode...")
    
    try:
        from planner import run_llm_query
        
        query = {
            'from': 'New Delhi, Delhi, India',
            'to': 'Mumbai, Maharashtra, India',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'preferences': {'prioritize': 'balanced'}
        }
        
        print("   Running LLM workflow (mock or real)...")
        result = run_llm_query(query)
        
        if result.get('error'):
            print(f"❌ LLM mode failed: {result['error']}")
            return False
        elif result.get('itineraries'):
            print("✅ LLM mode working")
            print(f"   Generated {len(result['itineraries'])} itinerary(ies)")
            
            # Check for LLM-specific features
            first_itinerary = result['itineraries'][0]
            if 'score' in first_itinerary:
                print(f"   ✅ LLM scoring present: {first_itinerary['score'].get('overall', 'N/A')}")
            if 'ranking_explanation' in first_itinerary:
                print(f"   ✅ LLM explanations present")
            
            return True
        else:
            print("❌ LLM mode failed - no itineraries generated")
            return False
            
    except Exception as e:
        print(f"❌ LLM mode failed: {str(e)}")
        return False

def test_auto_mode():
    """Test auto mode detection"""
    print("\n🎯 Testing Auto Mode...")
    
    try:
        from planner import run_query
        
        query = {
            'from': 'New Delhi, Delhi, India',
            'to': 'Chandigarh, Punjab, India',
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'preferences': {'prioritize': 'time'}
        }
        
        result = run_query(query, mode='auto')
        
        if result.get('error'):
            print(f"❌ Auto mode failed: {result['error']}")
            return False
        elif result.get('itineraries'):
            print("✅ Auto mode working")
            
            # Determine which mode was used
            sources = result.get('sources', [])
            if any('llm' in str(source).lower() for source in sources):
                print("   🧠 Auto-selected LLM mode")
            else:
                print("   🔗 Auto-selected traditional mode")
            
            return True
        else:
            print("❌ Auto mode failed - no itineraries generated")
            return False
            
    except Exception as e:
        print(f"❌ Auto mode failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Multi-Agent Travel Planner - LLM Integration Test")
    print("=" * 60)
    
    tests = [
        test_environment_setup,
        test_dependencies,
        test_workflow_import,
        test_llm_connection,
        test_traditional_mode,
        test_llm_mode,
        test_auto_mode
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in {test.__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your LLM integration is working perfectly!")
        print("\n💡 Next steps:")
        print("   1. Start the web server: python app.py")
        print("   2. Visit http://localhost:5000")
        print("   3. Select '🧠 LLM Agents' mode and test")
    elif passed >= total - 2:
        print("✅ Most tests passed! Your integration is mostly working.")
        print("   Check the failed tests above for any issues.")
    else:
        print("⚠️  Several tests failed. Please check your configuration.")
        print("\n🔧 Troubleshooting:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Set API key: export OPENAI_API_KEY='your_key_here'")
        print("   3. Check internet connection")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
