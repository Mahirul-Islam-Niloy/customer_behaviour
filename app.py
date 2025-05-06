from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:8001"])  # Allow your frontend to access API

# Load the dataset once
DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

# ✅ Root route (optional)
@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API. Try /api/data, /api/summary or /api/feedback/low</h2>"

# ✅ Paginated full dataset
@app.route('/api/data', methods=['GET'])
def get_full_data():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    end = start + limit
    total = len(df)

    return jsonify({
        'total_records': total,
        'page': page,
        'limit': limit,
        'data': df.iloc[start:end].to_dict(orient='records')
    })

# ✅ Summary statistics
@app.route('/api/summary', methods=['GET'])
def get_summary():
    summary = df.describe(include='all').to_dict()
    return jsonify(summary)

# ✅ Filter by feedback score + pagination
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

# ✅ Required for Render hosting
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)