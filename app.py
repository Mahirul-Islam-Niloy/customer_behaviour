from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# Load your dataset
DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

# Route 1: Return full dataset
@app.route('/api/data', methods=['GET'])
def get_full_data():
    return jsonify(df.to_dict(orient='records'))

# Route 2: Return statistical summary
@app.route('/api/summary', methods=['GET'])
def get_summary():
    summary = df.describe(include='all').to_dict()
    return jsonify(summary)

# Route 3: Return data filtered by FeedbackScore
@app.route('/api/feedback/<level>', methods=['GET'])
def get_feedback_level(level):
    filtered_df = df[df['FeedbackScore'].str.lower() == level.lower()]
    return jsonify(filtered_df.to_dict(orient='records'))
@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API!<br>Use endpoints like /api/data, /api/summary, or /api/feedback/low</h2>"

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)