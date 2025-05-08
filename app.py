from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8001",
    "https://lambent-moxie-c5f681.netlify.app"
])


DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API</h2>"

@app.route('/api/data', methods=['GET'])
def get_filtered_data():
    filtered = df.copy()

   
    country = request.args.get('country')
    gender = request.args.get('gender')
    age = request.args.get('age')
    satisfaction = request.args.get('satisfactionscore')
    feedbackscore = request.args.get('feedbackscore')
    loyaltylevel = request.args.get('loyalty')

    
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


@app.route('/api/summary', methods=['GET'])
def get_full_summary():
    numeric_summary = df.describe().to_dict()
    categorical_summary = df.describe(include=['object']).to_dict()
    summary = {**numeric_summary, **categorical_summary}
    return jsonify(summary)


@app.route('/api/summary/numeric', methods=['GET'])
def get_numeric_summary():
    return jsonify(df.describe().to_dict())


@app.route('/api/summary/categorical', methods=['GET'])
def get_categorical_summary():
    return jsonify(df.describe(include=['object']).to_dict())


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)