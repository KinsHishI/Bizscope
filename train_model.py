# train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib  
import sqlite3

conn = sqlite3.connect('business_data.db')
df = pd.read_sql_query("SELECT * FROM floating_population", conn)
conn.close()

df['date_numeric'] = df['date'].str.replace('-', '.').astype(float)

features = df[['date_numeric']]
target = df['population_count']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(features, target)

joblib.dump(model, 'floating_population_model.pkl')
print("AI 모델 학습 및 저장이 완료되었습니다: floating_population_model.pkl")