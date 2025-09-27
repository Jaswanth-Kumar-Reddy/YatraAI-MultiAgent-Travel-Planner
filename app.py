# app.py - YatraAI Flask Backend
# Smart Yatra Planning with AI-Powered Multi-Agent Intelligence
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from planner import run_query
import json
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load environment variables from .env if present
load_dotenv()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/plan', methods=['POST'])
def plan_trip():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['from', 'to', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Set default mode if not provided
        # Priority: llm > hybrid > api > static
        mode = data.get('mode', 'hybrid')
        
        # Auto-detect best mode if API keys are available
        if mode == 'auto':
            import os
            if os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'):
                mode = 'llm'  # LLM + Hybrid data (best experience)
            else:
                mode = 'hybrid'  # Real data without LLM (still great experience)
        
        # Create query
        query = {
            'from': data['from'],
            'to': data['to'],
            'date': data['date'],
            'preferences': data.get('preferences', {'prioritize': 'cost'})
        }
        
        # Run the planner
        result = run_query(query, mode=mode)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🚀 Starting YatraAI - Smart Yatra Planning with AI")
    print("🌐 Server running at: http://localhost:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)

