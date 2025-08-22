# core/analysis/population_predictor.py

import joblib
import pandas as pd
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'floating_population_model.pkl')
model = None

def load_model():
    """서버 시작 시 모델을 한 번만 불러오기 위한 함수"""
    global model
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print("AI Population model loaded successfully.")
        else:
            print(f"WARNING: Model file not found at {MODEL_PATH}")
    except Exception as e:
        print(f"ERROR: Could not load model. {e}")

def predict_population(year: int, quarter: int) -> float:
    """주어진 연도와 분기의 유동인구를 예측합니다."""
    if model is None:
        print("Model is not loaded. Returning 0.")
        return 0.0

    date_numeric = float(f"{year}.{quarter}")
    input_df = pd.DataFrame({'date_numeric': [date_numeric]})

    prediction = model.predict(input_df)
    
    return float(prediction[0])

load_model()