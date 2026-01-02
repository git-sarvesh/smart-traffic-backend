from flask import Flask, jsonify, request
from flask_cors import CORS
import time, threading, random, requests, os
from datetime import datetime
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# Google Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyAischy-MShK4jEr2DXSnNBe4RHxZpezg0')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Simulated ESP32 + Traffic state
traffic_state = {
    "active_lane": "NORTH",
    "remaining_time": 22,
    "lanes": {
        "NORTH": {"light": "GREEN", "density": 4, "count": 7},
        "SOUTH": {"light": "RED", "density": 1, "count": 3},
        "EAST": {"light": "RED", "density": 0, "count": 1},
        "WEST": {"light": "RED", "density": 2, "count": 5}
    },
    "emergency_active": False,
    "ai_counts": {"NORTH": 7, "SOUTH": 3, "EAST": 1, "WEST": 5}
}

# Load ML model
try:
    model = joblib.load('congestion_model.pkl')
except:
    model = None

def get_gemini_response(prompt):
    """Google Gemini AI Integration"""
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
    }
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
                        print(f'Gemini API Status: {response.status_code}, Response: {response.text}')
            
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return "Gemini AI: Service temporarily unavailable."
    except:
        return "Gemini AI: Connection error. Check API key."
                    print(f'Gemini API Exception: {e}')
        

def simulate_vehicle_detection():
    lanes = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    for lane in lanes:
        traffic_state['ai_counts'][lane] = random.randint(0, 12)

def simulate_esp32_update():
    lanes = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    if not traffic_state['emergency_active']:
        densities = {lane: random.randint(0, 5) for lane in lanes}
        max_lane = max(densities, key=densities.get)
if traffic_state['active_lane'] != max_lane:
            traffic_state['active_lane'] = max_lane
            traffic_state['remaining_time'] = 10 + (3 * densities[max_lane])
                 traffic_state['lanes'][lane]['density'] = densities[lane]
    traffic_state['remaining_time'] -= 1
    if traffic_state['remaining_time'] <= 0:
                traffic_state['emergency_active'] = False
                traffic_state['remaining_time'] = 22
    
def congestion_prediction():
    if model:
        hour = datetime.now().hour
        day = datetime.now().weekday()
        pred = model.predict([[hour, day, np.mean(list(traffic_state['ai_counts'].values()))]])[0]
        confidence = 0.82
        levels = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
        return levels.get(pred, "MEDIUM"), confidence
    return "MEDIUM", 0.75

def update_loop():
    while True:
        simulate_vehicle_detection()
        simulate_esp32_update()
        time.sleep(2)

threading.Thread(target=update_loop, daemon=True).start()

@app.route('/api/status')
def status():
    pred_level, confidence = congestion_prediction()
    return jsonify({
        **traffic_state,
        "congestion": {"level": pred_level, "confidence": confidence},
        "timestamp": time.time()
    })

@app.route('/api/emergency', methods=['POST'])
def emergency():
    data = request.json
    target_lane = data.get('lane', 'NORTH')
    traffic_state['emergency_active'] = True
    traffic_state['active_lane'] = target_lane
    traffic_state['remaining_time'] = 20
    return jsonify({"status": "EMERGENCY ACTIVATED", "lane": target_lane})

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    data = request.json
    user_message = data.get('message', '')
    context = f"""
    🚦 SMART TRAFFIC SYSTEM - GOOGLE GEMINI AI ANALYST
    
    LIVE DATA:
    Active: {traffic_state['active_lane']} (GREEN {traffic_state['remaining_time']}s)
    Counts: N:{traffic_state['ai_counts']['NORTH']} S:{traffic_state['ai_counts']['SOUTH']} E:{traffic_state['ai_counts']['EAST']} W:{traffic_state['ai_counts']['WEST']}
    Density: N:{traffic_state['lanes']['NORTH']['density']} S:{traffic_state['lanes']['SOUTH']['density']} E:{traffic_state['lanes']['EAST']['density']} W:{traffic_state['lanes']['WEST']['density']}
    Emergency: {'ACTIVE' if traffic_state['emergency_active'] else 'INACTIVE'}
    Prediction: {congestion_prediction()[0]}
    
    QUESTION: {user_message}
    
    Answer as traffic engineer. Be specific and actionable.
    """
    ai_response = get_gemini_response(context)
    return jsonify({"response": ai_response, "timestamp": time.time()})

if __name__ == '__main__':
    print("🚦 Smart Traffic + Google Gemini AI → http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
 
