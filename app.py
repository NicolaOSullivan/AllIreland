from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Simple file-based storage
DATA_FILE = 'predictions.json'
RESULTS_FILE = 'results.json'

MATCHES = [
    {"id": 1, "home": "Cork", "away": "Galway"},
    {"id": 2, "home": "Limerick", "away": "Clare"},
    {"id": 3, "home": "Mayo", "away": "Louth"},
    {"id": 4, "home": "Kerry", "away": "Dublin"},
]

# Admin password - change this!
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'flutter2024')

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_predictions():
    return load_data(DATA_FILE)

def save_prediction(name, picks):
    predictions = get_predictions()
    predictions[name.strip()] = {
        "picks": picks,
        "timestamp": datetime.now().isoformat()
    }
    save_data(DATA_FILE, predictions)

def get_results():
    return load_data(RESULTS_FILE)

def save_results(results):
    save_data(RESULTS_FILE, results)

def calculate_scores():
    predictions = get_predictions()
    results = get_results()
    scores = []
    
    for name, data in predictions.items():
        correct = 0
        for match_id, pick in data['picks'].items():
            if results.get(match_id) == pick:
                correct += 1
        scores.append({"name": name, "score": correct, "picks": data['picks']})
    
    return sorted(scores, key=lambda x: (-x['score'], x['name']))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/play', methods=['GET', 'POST'])
def play():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            return render_template('play.html', matches=MATCHES, error="Please enter your name")
        
        predictions = get_predictions()
        if name.lower() in [n.lower() for n in predictions.keys()]:
            return render_template('play.html', matches=MATCHES, error="This name is already taken!")
        
        session['player_name'] = name
        return redirect(url_for('predict'))
    
    return render_template('play.html', matches=MATCHES)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    name = session.get('player_name')
    if not name:
        return redirect(url_for('play'))
    
    if request.method == 'POST':
        picks = {}
        for match in MATCHES:
            pick = request.form.get(f'match_{match["id"]}')
            if pick:
                picks[str(match['id'])] = pick
        
        if len(picks) != len(MATCHES):
            return render_template('predict.html', matches=MATCHES, name=name, 
                                 error="Please pick a winner for all matches")
        
        save_prediction(name, picks)
        return redirect(url_for('confirmed'))
    
    return render_template('predict.html', matches=MATCHES, name=name)

@app.route('/confirmed')
def confirmed():
    name = session.get('player_name')
    predictions = get_predictions()
    player_data = predictions.get(name, {})
    return render_template('confirmed.html', name=name, picks=player_data.get('picks', {}), matches=MATCHES)

@app.route('/leaderboard')
def leaderboard():
    scores = calculate_scores()
    results = get_results()
    return render_template('leaderboard.html', scores=scores, matches=MATCHES, results=results)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error="Wrong password")
    
    if session.get('is_admin'):
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_login.html')

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'set_results':
            results = {}
            for match in MATCHES:
                winner = request.form.get(f'result_{match["id"]}')
                if winner:
                    results[str(match['id'])] = winner
            save_results(results)
        
        elif action == 'clear_all':
            save_data(DATA_FILE, {})
            save_data(RESULTS_FILE, {})
    
    predictions = get_predictions()
    results = get_results()
    scores = calculate_scores()
    
    return render_template('admin_panel.html', matches=MATCHES, predictions=predictions, 
                         results=results, scores=scores)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
