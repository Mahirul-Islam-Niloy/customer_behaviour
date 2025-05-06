from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app, origins=["http://localhost:8001"])

# Load dataset
DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API. Try /api/data, /api/summary, or /api/feedback/high</h2>"

# 🔍 Filterable API endpoint
@app.route('/api/data', methods=['GET'])
def get_filtered_data():
    filtered = df.copy()

    # Extract query parameters
    country = request.args.get('country')
    gender = request.args.get('gender')
    feedback = request.args.get('feedbackscore')
    loyalty = request.args.get('loyalty')
    age = request.args.get('age')
    satisfaction = request.args.get('satisfactionscore')

    # Apply filters
    if country:
        filtered = filtered[filtered['Country'].str.lower() == country.lower()]
    if gender:
        filtered = filtered[filtered['Gender'].str.lower() == gender.lower()]
    if feedback:
        filtered = filtered[filtered['FeedbackScore'].str.lower() == feedback.lower()]
    if loyalty:
        filtered = filtered[filtered['LoyaltyLevel'].str.lower() == loyalty.lower()]
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

# 📊 Summary stats
@app.route('/api/summary', methods=['GET'])
def get_summary():
    return jsonify(df.describe(include='all').to_dict())

# 🎯 Feedback score filter (Low, Medium, High)
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

# 🌐 Dynamic port support for Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)