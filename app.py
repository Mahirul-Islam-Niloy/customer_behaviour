from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8001",
    "https://lambent-moxie-c5f681.netlify.app"
])

DATA_PATH = 'customer_feedback_satisfaction.csv'
df = pd.read_csv(DATA_PATH)

def preprocess_data():
    if 'BehaviorType' not in df.columns:
        print("Creating BehaviorType column...")

        def label_adverse(row):
            first_group = (
                (row['ProductQuality'] >= 9 and row['FeedbackScore'] in ['Low', 'Medium']) or
                (row['ServiceQuality'] >= 9 and row['SatisfactionScore'] < 90)
            )
            second_group = (
                row['LoyaltyLevel'] == 'Gold' and
                row['PurchaseFrequency'] < 14
            )
            partially_adverse_condition = (
                (row['ProductQuality'] < 4 and row['FeedbackScore'] in ['High', 'Medium']) or
                (row['ServiceQuality'] < 5 and row['SatisfactionScore'] > 90)
            )
            if first_group and second_group:
                return 'Adverse'
            elif partially_adverse_condition:
                return 'Partially Adverse'
            else:
                return 'Normal'

        df['BehaviorType'] = df.apply(label_adverse, axis=1)
        print("BehaviorType column created successfully.")

preprocess_data()

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
@app.route('/api/adverse-count', methods=['GET'])
def get_adverse_count():
    try:
        adverse_customers = df[df['BehaviorType'] == 'Adverse']
        count = len(adverse_customers)
        return jsonify({"adverse_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/api/patterns', methods=['GET'])
def get_pattern_rules():
    if not MLXTEND_AVAILABLE:
        return jsonify({"error": "mlxtend library not installed"}), 500

    df_copy = df.copy()

    def bin_quality(x):
        return 'High' if x >= 9 else 'Low'

    def bin_satisfaction(x):
        return 'High' if x >= 90 else 'Low'

    def bin_frequency(x):
        return 'High' if x >= 15 else 'Low'
    

    df_copy['ProductQuality_Bin'] = df_copy['ProductQuality'].apply(bin_quality)
    df_copy['ServiceQuality_Bin'] = df_copy['ServiceQuality'].apply(bin_quality)
    df_copy['Satisfaction_Bin'] = df_copy['SatisfactionScore'].apply(bin_satisfaction)
    df_copy['PurchaseFreq_Bin'] = df_copy['PurchaseFrequency'].apply(bin_frequency)
    df_copy['Feedback_Bin'] = df_copy['FeedbackScore'].str.strip().str.title()

    def label_adverse(row):
        first_group = (
            (row['ProductQuality'] >= 9 and row['FeedbackScore'] in ['Low', 'Medium']) or
            (row['ServiceQuality'] >= 9 and row['SatisfactionScore'] < 90)
        )
        second_group = (
            row['LoyaltyLevel'] == 'Gold' and
            row['PurchaseFrequency'] < 14
        )
        if first_group and second_group:
            return 'True'
        return 'False'

    df_copy['Adverse'] = df_copy.apply(label_adverse, axis=1)

    transactions = []
    for _, row in df_copy.iterrows():
        transactions.append([
            f"ProductQuality={row['ProductQuality_Bin']}",
            f"ServiceQuality={row['ServiceQuality_Bin']}",
            f"Satisfaction={row['Satisfaction_Bin']}",
            f"Feedback={row['Feedback_Bin']}",
            f"PurchaseFreq={row['PurchaseFreq_Bin']}",
            f"Adverse={row['Adverse']}"
        ])

    from mlxtend.preprocessing import TransactionEncoder
    from mlxtend.frequent_patterns import apriori, association_rules

    te = TransactionEncoder()
    te_array = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_array, columns=te.columns_)

    frequent_itemsets = apriori(df_encoded, min_support=0.1, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.6)

    adverse_rules = rules[rules['consequents'].astype(str).str.contains("Adverse=True")]
    adverse_rules = adverse_rules.sort_values(by="lift", ascending=False)

    adverse_rules['antecedents'] = adverse_rules['antecedents'].apply(lambda x: list(x))
    adverse_rules['consequents'] = adverse_rules['consequents'].apply(lambda x: list(x))

    top_rules = adverse_rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head(10)

    return jsonify(top_rules.to_dict(orient='records'))

@app.route('/api/behavior-stats', methods=['GET'])
def get_behavior_stats():
    try:
        if 'BehaviorType' not in df.columns:
            raise KeyError("'BehaviorType' column not found")

        total_customers = len(df)
        adverse_customers = df[df['BehaviorType'] == 'Adverse']
        partially_adverse_customers = df[df['BehaviorType'] == 'Partially Adverse']
        normal_customers = df[df['BehaviorType'] == 'Normal']

        adverse_percentage = (len(adverse_customers) / total_customers) * 100
        partially_adverse_percentage = (len(partially_adverse_customers) / total_customers) * 100
        normal_percentage = (len(normal_customers) / total_customers) * 100

        return jsonify({
            "adverse_percentage": adverse_percentage,
            "partially_adverse_percentage": partially_adverse_percentage,
            "normal_percentage": normal_percentage,
            "total_customers": total_customers
        })
    except Exception as e:
        print("Error in calculating behavior stats:", e)
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/api/adverse-customers', methods=['GET'])
def get_adverse_customers():
   
    adverse_customers = df[df['BehaviorType'] == 'Adverse']

   
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    end = start + limit

    
    paginated = adverse_customers.iloc[start:end]

    return jsonify({
        "total_records": len(adverse_customers),
        "page": page,
        "limit": limit,
        "data": paginated.to_dict(orient='records')
    })
@app.route('/api/behavior-rules', methods=['GET'])
def get_behavior_rules():
    rules = {
        "Adverse": [
            "ProductQuality >= 9 AND FeedbackScore in ['Low', 'Medium']",
            "ServiceQuality >= 9 AND SatisfactionScore < 90",
            "LoyaltyLevel == 'Gold' AND PurchaseFrequency < 14"
        ],
        "Partially Adverse": [
            "ProductQuality < 4 AND FeedbackScore in ['High', 'Medium']",
            "ServiceQuality < 5 AND SatisfactionScore > 90"
        ]
    }
    return jsonify(rules)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
