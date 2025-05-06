from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

# Initialize Flask app and enable CORS for frontend
app = Flask(__name__)
CORS(app, origins=["http://localhost:8001"])

# Load the dataset once at startup
DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API</h2>"

# 🔍 Filtered data endpoint
@app.route('/api/data', methods=['GET'])
def get_filtered_data():
    filtered = df.copy()

    # Extract filter parameters
    country = request.args.get('country')
    gender = request.args.get('gender')
    age = request.args.get('age')
    satisfaction = request.args.get('satisfactionscore')
    feedbackscore = request.args.get('feedbackscore')
    loyaltylevel = request.args.get('loyalty')

    # Apply filters
    if country:
        filtered = filtered[filtered['Country'].str.lower() == country.lower()]
    if gender:
        filtered = filtered[filtered['Gender'].str.lower() == gender.lower()]
    if age:
        try:
            filtered = filtered[filtered['Age'] == int(age)]
        except:
            pass
    if satisfaction:
        try:
            filtered = filtered[filtered['SatisfactionScore'] == float(satisfaction)]
        except:
            pass
    if feedbackscore:
        filtered = filtered[filtered['FeedbackScore'].str.lower() == feedbackscore.lower()]
    if loyaltylevel:
        filtered = filtered[filtered['LoyaltyLevel'].str.lower() == loyaltylevel.lower()]

    # Pagination
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    end = start + limit
    total = len(filtered)

    return jsonify({
        'total_records': total,
        'page': page,
        'limit': limit,
        'data': filtered.iloc[start:end].to_dict(orient='records')
    })

# 📊 Clean summary stats as JSON
@app.route('/api/summary', methods=['GET'])
def get_summary():
    summary = df.describe(include='all').reset_index()
    return jsonify(summary.to_dict(orient='records'))

# 🎯 Quick filter by feedback score (low/medium/high)
@app.route('/api/feedback/<level>', methods=['GET'])
def get_feedback_level(level):
    filtered = df[df['FeedbackScore'].str.lower() == level.lower()]
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    end = start + limit
    total = len(filtered)

    return jsonify({
        'total_records': total,
        'page': page,
        'limit': limit,
        'data': filtered.iloc[start:end].to_dict(orient='records')
    })

# 🌐 Use dynamic port for Render or fallback to 5000
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)