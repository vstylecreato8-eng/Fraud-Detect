from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add python directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from python.model import PredictionModel

app = Flask(__name__)
CORS(app)

# Initialize model
model = PredictionModel()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_available': model.model is not None,
        'timestamp': str(__import__('datetime').datetime.now())
    })

@app.route('/api/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        # Prepare input data
        input_data = {
            'transaction_amount': float(data.get('transaction_amount', 0)),
            'payment_method': str(data.get('payment_method', 'other')).lower(),
            'product_category': str(data.get('product_category', 'other')).lower(),
            'quantity': int(data.get('quantity', 1)),
            'customer_age': int(data.get('customer_age', 35)),
            'device_used': str(data.get('device_used', 'desktop')).lower(),
            'account_age_days': int(data.get('account_age_days', 35)),
            'transaction_hour': int(data.get('transaction_hour', 12)),
        }
        
        # Make prediction
        result = model.predict(input_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
