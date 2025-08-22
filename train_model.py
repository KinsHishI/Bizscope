# train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib  # 모델을 파일로 저장하는 라이브러리
import sqlite3

# 1. DB에서 데이터 불러오기
conn = sqlite3.connect('business_data.db')
df = pd.read_sql_query("SELECT * FROM floating_population", conn)
conn.close()

# 2. 데이터 전처리
# 'date'와 'time_slot'을 숫자형으로 변환하는 과정이 필요합니다.
# 예시: '2021년 4분기'를 2021.4 와 같이 변환
df['date_numeric'] = df['date'].str.replace('년', '.').str.replace('분기', '')

# 3. 모델 학습
# 'date_numeric'으로 'population_count'를 예측하도록 모델을 학습시킵니다.
features = df[['date_numeric']]
target = df['population_count']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(features, target)

# 4. 학습된 모델 저장
# .pkl 파일로 모델을 저장하여 나중에 불러와 사용할 수 있게 합니다.
joblib.dump(model, 'floating_population_model.pkl')
print("AI 모델 학습 및 저장이 완료되었습니다: floating_population_model.pkl")