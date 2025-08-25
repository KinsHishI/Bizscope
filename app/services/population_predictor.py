import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models", "floating_population_model.pkl"
)
_model = None


def load_model_once():
    global _model
    if _model is None and os.path.exists(MODEL_PATH):
        _model = joblib.load(MODEL_PATH)
        print("AI Population model loaded:", MODEL_PATH)


def predict_population(year: int, quarter: int) -> float:
    load_model_once()
    if _model is None:
        return 0.0
    date_numeric = float(f"{year}.{quarter}")
    X = pd.DataFrame({"date_numeric": [date_numeric]})
    y = _model.predict(X)
    return float(y[0])
