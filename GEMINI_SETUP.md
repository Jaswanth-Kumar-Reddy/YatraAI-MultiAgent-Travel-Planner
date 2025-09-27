# 🆓 Google Gemini Integration Guide

## Why Google Gemini?

✅ **FREE TIER**: 15 requests per minute, 1500 requests per day  
✅ **No Credit Card Required**: Unlike OpenAI and Anthropic  
✅ **Excellent Performance**: Gemini-1.5-Flash is fast and intelligent  
✅ **Perfect for Learning**: Ideal for students and developers  

## 🚀 Quick Setup (2 minutes)

### Step 1: Get Your Free API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### Step 2: Configure Your Project
1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your key:
   ```bash
   # Google Gemini Configuration (FREE!)
   LLM_PROVIDER=google
   GOOGLE_API_KEY=your_actual_api_key_here
   LLM_MODEL=gemini-1.5-flash
   ```

### Step 3: Test It Works
```bash
python3 test_llm_integration.py
```

You should see:
```
✅ LLM Provider: google
✅ LLM Model: gemini-1.5-flash
```

## 🎯 Available Gemini Models

### **gemini-1.5-flash** (Recommended)
- ⚡ **Fast**: Quick responses
- 🆓 **Free**: 15 requests/minute
- 🎯 **Smart**: Great for travel planning
- 💰 **Cost**: FREE

### **gemini-1.5-pro** (Advanced)
- 🧠 **Smarter**: Better reasoning
- 🆓 **Free**: 2 requests/minute
- 📊 **Complex**: Handles detailed itineraries
- 💰 **Cost**: FREE (limited)

### **gemini-1.0-pro** (Basic)
- 📝 **Simple**: Basic tasks
- 🆓 **Free**: Higher limits
- ⚡ **Fast**: Quick responses
- 💰 **Cost**: FREE

## 🔧 Configuration Options

### Basic Configuration
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_here
LLM_MODEL=gemini-1.5-flash
```

### Advanced Configuration
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_here
LLM_MODEL=gemini-1.5-pro
DEBUG_MODE=true
```

## 🎉 What You Get

### **Intelligent Travel Planning**
- 🤖 **Smart Mode Selection**: AI chooses best transport modes
- 📋 **Optimized Itineraries**: Multiple options with reasoning
- 🏆 **Preference-Based Ranking**: Personalized recommendations
- 💡 **Detailed Explanations**: Why each option is recommended

### **Example AI Response**
```json
{
  "ranking_explanation": "Best balance of cost (₹1200) and time (8h 30m)",
  "recommendations": ["Book early for better deals", "Consider window seat"],
  "score": {
    "cost": 0.85,
    "time": 0.72,
    "comfort": 0.90,
    "overall": 0.82
  }
}
```

## 🆚 Comparison with Paid Options

| Feature | Gemini (FREE) | GPT-4 (PAID) | Claude (PAID) |
|---------|---------------|---------------|---------------|
| **Cost** | 🆓 FREE | 💰 $0.03/1K tokens | 💰 $0.015/1K tokens |
| **Speed** | ⚡ Fast | ⚡ Fast | 🐌 Medium |
| **Quality** | 🎯 Excellent | 🏆 Best | 🎯 Excellent |
| **Limits** | 15/min, 1500/day | Pay per use | Pay per use |
| **Setup** | 🚀 2 minutes | 💳 Credit card required | 💳 Credit card required |

## 🔍 Troubleshooting

### "No API key found"
- Make sure you created `.env` file (not `.env.example`)
- Check that `GOOGLE_API_KEY=` has your actual key
- No quotes needed around the key

### "Rate limit exceeded"
- Gemini free tier: 15 requests/minute
- Wait a minute and try again
- Consider upgrading to gemini-1.5-pro for higher limits

### "Model not found"
- Use `gemini-1.5-flash` (recommended)
- Or try `gemini-1.0-pro` for basic usage
- Check Google AI Studio for available models

## 🎯 Next Steps

1. **Get your free API key** from Google AI Studio
2. **Configure your `.env` file** with the key
3. **Test the integration** with the test script
4. **Start planning trips** with AI-powered intelligence!

Your YatraAI project now has **FREE AI capabilities** that rival expensive paid services! 🚀
