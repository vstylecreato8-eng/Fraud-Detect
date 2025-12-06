from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
from model import PredictionModel
import csv
import io
import os


class Config:
    ORIGINS = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5173", "*"]
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging():
    logging.basicConfig(level=logging.INFO, format=Config.LOG_FORMAT)
    return logging.getLogger(__name__)


def initialize_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.ORIGINS,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    return app


def load_model(logger):
    try:
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        
        logger.info(f"Script dir: {script_dir}")
        logger.info(f"Parent dir: {parent_dir}")
        
        # Try multiple model file paths
        model_paths_to_try = [
            os.path.join(parent_dir, "model", "Credit.pickle"),
            os.path.join(parent_dir, "model", "Creditcard.model"),
            os.path.join(parent_dir, "model", "model.pkl"),
            os.path.join(parent_dir, "model", "model.joblib"),
            os.path.join(script_dir, "..", "model", "Credit.pickle"),
            os.path.join(script_dir, "..", "model", "Creditcard.model"),
        ]
        
        model_path = None
        for path in model_paths_to_try:
            logger.info(f"Checking: {path}")
            if os.path.exists(path):
                model_path = path
                logger.info(f"Found model file: {path}")
                break
        
        if model_path is None:
            logger.error(f"No model file found. Tried: {model_paths_to_try}")
            return None
        
        model = PredictionModel(model_path)
        logger.info(f"Model initialized successfully (path: {model_path})")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}", exc_info=True)
        return None


logger = setup_logging()
app = initialize_app()
model = load_model(logger)


def transform_frontend_data(frontend_data):
    logger.info(f"Transforming: {frontend_data}")
    
    if 'transaction_amount' in frontend_data or 'amount' in frontend_data:
        return {
            'transaction_amount': float(frontend_data.get('transaction_amount') or frontend_data.get('amount', 0)),
            'payment_method': frontend_data.get('payment_method', 'other').lower(),
            'product_category': frontend_data.get('product_category', 'other').lower(),
            'quantity': int(frontend_data.get('quantity', 1)),
            'customer_age': int(frontend_data.get('customer_age') or frontend_data.get('account_age', 35)),
            'device_used': frontend_data.get('device_used', 'desktop').lower(),
            'account_age_days': int(frontend_data.get('account_age_days') or frontend_data.get('account_age', 35)),
            'transaction_hour': int(frontend_data.get('transaction_hour', 12)),
        }
    
    return {
        'transaction_amount': 0,
        'payment_method': 'other',
        'product_category': 'other',
        'quantity': 1,
        'customer_age': 35,
        'device_used': 'desktop',
        'account_age_days': 35,
        'transaction_hour': 12,
    }


@app.route('/', methods=['GET'])
def root():
    return jsonify({'status': 'Fraud Detection API is running'}), 200


@app.route('/api/debug', methods=['GET'])
def debug():
    return jsonify({
        'status': 'debug',
        'model_loaded': model is not None,
        'model_type': str(type(model)) if model else None,
        'timestamp': datetime.now().isoformat(),
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None
    }), 200


@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded', 'status': 'error'}), 503

        if 'file' in request.files:
            return handle_csv_upload()

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided', 'status': 'error'}), 400

        transaction_data = transform_frontend_data(data)
        result = model.predict(transaction_data)
        
        return jsonify({
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'risk_score': result['risk_score'],
            'risk_level': result.get('risk_level'),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }), 200

    except ValueError as ve:
        logger.warning(f"Validation error: {str(ve)}")
        return jsonify({'error': str(ve), 'status': 'error'}), 400
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e), 'status': 'error'}), 500


def handle_csv_upload():
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected', 'status': 'error'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files supported', 'status': 'error'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_data = csv.DictReader(stream)
        results = []
        
        for row in csv_data:
            try:
                form_fields = {
                    'payment_method': request.form.get('payment_method'),
                    'account_age': request.form.get('account_age'),
                    'card_number': request.form.get('card_number'),
                    'transaction_hour': request.form.get('transaction_hour'),
                    'amount': row.get('amount', 0),
                }
                
                transaction_data = transform_frontend_data(form_fields)
                result = model.predict(transaction_data)
                
                results.append({
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'risk_score': result['risk_score'],
                    'risk_level': result.get('risk_level'),
                    'row_data': row
                })
            except Exception as e:
                logger.error(f"Row prediction error: {str(e)}")
                results.append({'error': str(e), 'prediction': None, 'row_data': row})
        
        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"CSV parsing error: {str(e)}")
        return jsonify({'error': f'CSV parsing failed: {str(e)}', 'status': 'error'}), 400


@app.route('/api/predict/batch', methods=['POST'])
def predict_batch():
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded', 'status': 'error'}), 503

        data = request.get_json()
        transactions = data.get('transactions', [])

        if not transactions:
            return jsonify({'error': 'No transactions provided', 'status': 'error'}), 400

        logger.info(f"Processing {len(transactions)} batch predictions")
        results = []
        
        for idx, transaction in enumerate(transactions):
            try:
                if 'payment_method' in transaction or 'account_age' in transaction:
                    transaction = transform_frontend_data(transaction)
                
                result = model.predict(transaction)
                results.append({
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'risk_score': result['risk_score'],
                    'risk_level': result.get('risk_level', 'unknown')
                })
            except Exception as e:
                logger.error(f"Batch error [{idx+1}]: {str(e)}")
                results.append({
                    'error': str(e),
                    'prediction': None,
                    'confidence': 0,
                    'risk_score': 0,
                    'risk_level': 'unknown'
                })

        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }), 200

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error', 'details': str(e), 'status': 'error'}), 500


@app.route('/api/model/info', methods=['GET'])
def model_info():
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded', 'status': 'error'}), 503

        info = model.get_info()
        return jsonify({'info': info, 'status': 'success'}), 200

    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e), 'status': 'error'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'status': 'error'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'status': 'error'}), 500


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
