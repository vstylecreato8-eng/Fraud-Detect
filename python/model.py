"""
Prediction Model Module
Handles machine learning model initialization and predictions
Uses Random Forest Classifier with Random Under Sampling
"""
import numpy as np
import logging
from typing import Dict, Any, List
import pickle
import os
from datetime import datetime
import sys
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# Try importing sklearn/joblib
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False
    logger.warning("joblib not available, will use pickle")


class PredictionModel:
    
    def __init__(self, model_path: str = None):
        
        self.model_path = model_path or 'Creditcard.model'
        self.model = None
        self.scaler = None
        # Updated feature names to match Random Forest Classifier (RFE)
        # These correspond to CSV columns: Transaction_Amount, Payment_Method, 
        # Product_Category, Quantity, Customer_Age, Device_Used, Account_Age_Days, Transaction_Hour
        self.feature_names = [
            'transaction_amount',
            'payment_method',
            'product_category',
            'quantity',
            'customer_age',
            'device_used',
            'account_age_days',
            'transaction_hour'
        ]
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
        
        self._load_model()
    
    def _load_model(self):

        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            
            logger.info(f"Attempting to load Random Forest model from {self.model_path}")
            
            # Try joblib first
            if HAS_JOBLIB:
                try:
                    logger.info("Attempting to load with joblib...")
                    self.model = joblib.load(self.model_path)
                    logger.info(f"✓ Model successfully loaded with joblib")
                    logger.info(f"Model type: {type(self.model)}")
                    logger.info(f"Model: {str(self.model)[:100]}...")
                    return
                except Exception as e:
                    logger.warning(f"joblib load failed: {str(e)}")
            
            # Fallback to pickle
            try:
                logger.info("Attempting to load with pickle...")
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                logger.info(f"✓ Model successfully loaded with pickle")
                logger.info(f"Model type: {type(self.model)}")
                return
            except Exception as e:
                logger.error(f"Pickle load failed: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"✗ Error loading model: {str(e)}")
            logger.warning(f"⚠ Model will NOT be available - using fallback scoring mode")
            self.model = None
    
    def _create_fallback_model(self):
        return {
            'type': 'fallback',
            'version': '1.0',
            'created': datetime.now().isoformat()
        }
    
    def _encode_categorical(self, category: str, category_type: str) -> int:

        payment_methods = {
            'debit card': 1,
            'credit card': 2,
            'paypal': 3,
            'bank transfer': 4,
            'other': 0
        }
        
        product_categories = {
            'home & garden': 1,
            'health & beauty': 2,
            'toys & games': 3,
            'clothing': 4,
            'electronics': 5,
            'other': 0
        }
        
        device_types = {
            'mobile': 1,
            'tablet': 2,
            'desktop': 3,
            'other': 0
        }
        
        if category_type == 'payment_method':
            return payment_methods.get(category.lower(), 0)
        elif category_type == 'product_category':
            return product_categories.get(category.lower(), 0)
        elif category_type == 'device_used':
            return device_types.get(category.lower(), 0)
        
        return 0
    
    def _extract_features(self, data: Dict[str, Any]) -> List[float]:

        # Log the incoming data
        logger.info(f"Extracting features from: {data}")
        
        # Transaction Amount (required)
        try:
            transaction_amount = float(data.get('transaction_amount', 0))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid transaction_amount value: {data.get('transaction_amount')}")
        
        # Payment Method
        payment_method = str(data.get('payment_method', 'other')).lower()
        payment_encoded = self._encode_categorical(payment_method, 'payment_method')
        
        # Product Category
        product_category = str(data.get('product_category', 'other')).lower()
        product_encoded = self._encode_categorical(product_category, 'product_category')
        
        # Quantity
        try:
            quantity = int(data.get('quantity', 1))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid quantity value: {data.get('quantity')}")
        
        # Customer Age
        try:
            customer_age = int(data.get('customer_age', 35))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid customer_age value: {data.get('customer_age')}")
        
        # Device Used
        device_used = str(data.get('device_used', 'desktop')).lower()
        device_encoded = self._encode_categorical(device_used, 'device_used')
        
        # Account Age Days
        try:
            account_age_days = int(data.get('account_age_days', 35))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid account_age_days value: {data.get('account_age_days')}")
        
        # Transaction Hour
        try:
            transaction_hour = int(data.get('transaction_hour', 12))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid transaction_hour value: {data.get('transaction_hour')}")
        
        # Validate ranges
        if transaction_amount < 0:
            raise ValueError("Amount cannot be negative")
        if not (0 <= customer_age <= 120):
            raise ValueError(f"Customer age must be between 0 and 120, got {customer_age}")
        if not (0 <= transaction_hour < 24):
            raise ValueError(f"Hour of day must be between 0 and 23, got {transaction_hour}")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if account_age_days < 0:
            raise ValueError("Account age cannot be negative")
        
        # Build feature list in order for model
        features = [
            transaction_amount,
            payment_encoded,
            product_encoded,
            quantity,
            customer_age,
            device_encoded,
            account_age_days,
            transaction_hour
        ]
        
        logger.info(f"Extracted features: {features}")
        logger.info(f"Feature mapping: transaction_amount={transaction_amount}, "
                   f"payment_method={payment_method}({payment_encoded}), "
                   f"product_category={product_category}({product_encoded}), "
                   f"quantity={quantity}, customer_age={customer_age}, "
                   f"device_used={device_used}({device_encoded}), "
                   f"account_age_days={account_age_days}, transaction_hour={transaction_hour}")
        return features
    
    def _calculate_risk_score(self, features: List[float]) -> float:

        try:
            # Try to use actual model if available
            if self.model is not None:
                try:
                    # Convert features to numpy array for model prediction
                    import numpy as np
                    features_array = np.array([features])
                    
                    # Try different predict methods for Random Forest
                    if hasattr(self.model, 'predict_proba'):
                        # For sklearn Random Forest Classifier
                        logger.info("Using Random Forest Classifier with predict_proba()")
                        probabilities = self.model.predict_proba(features_array)
                        # Get probability of fraud class (usually class 1)
                        risk_score = float(probabilities[0][1]) if probabilities.shape[1] > 1 else float(probabilities[0][0])
                    elif hasattr(self.model, 'predict'):
                        # For other models
                        logger.info("Using model.predict()")
                        prediction = self.model.predict(features_array)
                        risk_score = float(prediction[0])
                    else:
                        # Try calling the model directly
                        logger.info("Calling model directly")
                        prediction = self.model(features_array)
                        risk_score = float(prediction[0])
                    
                    # Ensure score is between 0 and 1
                    risk_score = max(0.0, min(1.0, risk_score))
                    logger.info(f"✓ Model prediction successful: {risk_score:.3f}")
                    return round(risk_score, 3)
                    
                except Exception as e:
                    logger.error(f"Error using model for prediction: {str(e)}")
                    logger.warning("Falling back to rule-based scoring")
        
        except Exception as e:
            logger.error(f"Error in model prediction attempt: {str(e)}")
        
        # Fallback: Rule-based scoring (ONLY if model is not available)
        logger.warning("⚠ Using FALLBACK rule-based scoring (Random Forest model not available)")
        transaction_amount = features[0]
        # payment_encoded = features[1]
        # product_encoded = features[2]
        quantity = features[3]
        customer_age = features[4]
        # device_encoded = features[5]
        account_age_days = features[6]
        transaction_hour = features[7]
        
        risk_score = 0.0
        
        # Amount-based risk
        if transaction_amount > 2000:
            risk_score += 0.3
        elif transaction_amount > 1000:
            risk_score += 0.2
        elif transaction_amount > 500:
            risk_score += 0.1
        
        # Quantity-based risk
        if quantity > 100:
            risk_score += 0.15
        
        # Age-based risk
        if customer_age < 25:
            risk_score += 0.1
        
        # Account age risk (newer accounts riskier)
        if account_age_days < 30:
            risk_score += 0.2
        elif account_age_days < 90:
            risk_score += 0.1
        
        # Hour-based risk (unusual hours)
        if transaction_hour < 6 or transaction_hour > 22:
            risk_score += 0.1
        
        risk_score = min(risk_score, 1.0)
        return round(risk_score, 3)
    
    def _get_risk_level(self, risk_score: float) -> str:

        if risk_score < self.risk_thresholds['low']:
            return 'low'
        elif risk_score < self.risk_thresholds['medium']:
            return 'medium'
        else:
            return 'high'
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:

        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"PREDICTION REQUEST - Random Forest Classifier")
            logger.info(f"{'='*70}")
            logger.info(f"Input data: {data}")
            
            if self.model is None:
                logger.warning("⚠ MODEL NOT LOADED - Using fallback scoring")
            else:
                logger.info(f"✓ Model is loaded: {type(self.model).__name__}")
            
            # Extract features
            features = self._extract_features(data)
            logger.info(f"Features extracted: {features}")
            
            # Get prediction from model
            if self.model is not None and hasattr(self.model, 'predict_proba'):
                try:
                    features_array = np.array([features])
                    # Get probability of SAFE class (class 0)
                    probabilities = self.model.predict_proba(features_array)
                    safe_probability = float(probabilities[0][0])  # Probability of SAFE
                    fraud_probability = float(probabilities[0][1]) if probabilities.shape[1] > 1 else (1.0 - safe_probability)
                    
                    logger.info(f"Model probabilities - SAFE: {safe_probability:.3f}, FRAUD: {fraud_probability:.3f}")
                    
                    # Confidence is the probability of SAFE class
                    confidence = safe_probability
                    
                    # Decision: if confidence (safe probability) < 70%, it's FRAUD
                    if confidence < 0.7:
                        prediction = "FRAUD"
                        risk_score = fraud_probability
                    else:
                        prediction = "SAFE"
                        risk_score = fraud_probability
                    
                except Exception as e:
                    logger.error(f"Error getting model probability: {str(e)}")
                    # Fallback to risk score method
                    risk_score = self._calculate_risk_score(features)
                    confidence = max(0.5, 1.0 - risk_score) if risk_score < 0.5 else risk_score
                    prediction = "FRAUD" if confidence < 0.7 else "SAFE"
            else:
                # Use risk score as fallback
                risk_score = self._calculate_risk_score(features)
                # Risk score is probability of fraud
                # Confidence is probability of safe (1 - risk_score)
                confidence = max(0.01, 1.0 - risk_score)
                prediction = "FRAUD" if confidence < 0.7 else "SAFE"
                logger.info(f"Using fallback: Risk Score={risk_score:.3f}, Confidence={confidence:.3f}")
            
            # Determine risk level
            risk_level = self._get_risk_level(risk_score)
            
            logger.info(f"PREDICTION: {prediction}")
            logger.info(f"Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
            logger.info(f"Risk Score: {risk_score:.3f}")
            logger.info(f"Risk Level: {risk_level}")
            
            result = {
                'prediction': prediction,
                'confidence': round(float(confidence), 3),
                'risk_score': round(float(risk_score), 3),
                'risk_level': risk_level,
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'model_used': self.model is not None
            }
            
            logger.info(f"RESULT: {result}")
            logger.info(f"{'='*70}\n")
            return result
        
        except ValueError as e:
            logger.warning(f"Validation error during prediction: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}", exc_info=True)
            raise
    
    def predict_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make predictions on multiple transactions
        
        Args:
            data_list: List of transaction data dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        for data in data_list:
            try:
                result = self.predict(data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error predicting transaction: {str(e)}")
                results.append({
                    'error': str(e),
                    'prediction': None
                })
        
        return results
    
    def get_info(self) -> Dict[str, Any]:

        return {
            'model_type': 'Transaction Safety Prediction Model',
            'version': '1.0',
            'features': self.feature_names,
            'risk_thresholds': self.risk_thresholds,
            'model_loaded': self.model is not None,
            'model_path': self.model_path,
            'created': datetime.now().isoformat()
        }
    
    def update_model(self, model_path: str):

        self.model_path = model_path
        self._load_model()
        logger.info(f"Model updated from {model_path}")


# Example model training function (for reference)
def train_model(training_data: List[Dict], training_labels: List[int], output_path: str = 'trained_model.pkl'):
    logger.info("Training model...")
    # Your training logic here
    logger.info(f"Model training complete. Saved to {output_path}")
