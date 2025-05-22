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

# Preprocess the DataFrame and ensure BehaviorType is properly populated
def preprocess_data():
    # Check if 'BehaviorType' exists and apply the label_adverse function
    if 'BehaviorType' not in df.columns:
        print("Creating BehaviorType column...")

        def label_adverse(row):
            # Logic for labeling adverse behavior based on the conditions provided
            if ((row['ProductQuality'] >= 9 and row['FeedbackScore'] in ['Low', 'Medium']) or 
                (row['ServiceQuality'] >= 9 and row['SatisfactionScore'] < 90)):
                if (row['LoyaltyLevel'] == 'Gold' and row['PurchaseFrequency'] < 15):
                    return 'Adverse'
            return 'Normal'

        # Apply the label_adverse function to create the BehaviorType column
        df['BehaviorType'] = df.apply(label_adverse, axis=1)

        print("BehaviorType column created successfully.")

# Apply the preprocessing before handling API requests
preprocess_data()

@app.route('/')
def home():
    return "<h2>Welcome to the Customer Feedback API</h2>"

# Endpoint to get filtered customer data
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

# Endpoint to get adverse behavior stats
@app.route('/api/behavior-stats', methods=['GET'])
def get_behavior_stats():
    try:
        total_customers = len(df)
        adverse_customers = df[df['BehaviorType'] == 'Adverse']
        normal_customers = df[df['BehaviorType'] == 'Normal']

        adverse_percentage = (len(adverse_customers) / total_customers) * 100
        normal_percentage = (len(normal_customers) / total_customers) * 100

        return jsonify({
            "adverse_percentage": adverse_percentage,
            "normal_percentage": normal_percentage,
            "total_customers": total_customers
        })
    except Exception as e:
        print("Error in calculating behavior stats:", e)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
