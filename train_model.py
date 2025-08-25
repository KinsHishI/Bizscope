# train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib  # scikit-learn 모델을 저장하고 불러오기 위한 라이브러리
import sqlite3

# 1. 데이터베이스에서 유동인구 데이터 로드
conn = sqlite3.connect('business_data.db')
df = pd.read_sql_query("SELECT * FROM floating_population", conn)
conn.close()

# 2. 특성 공학(Feature Engineering): 날짜 문자열을 숫자형으로 변환
# 예: '2022-4' -> 2022.4. 모델이 학습할 수 있는 숫자 형태로 만듭니다.
df['date_numeric'] = df['date'].str.replace('-', '.').astype(float)

# 3. 학습에 사용할 특성(X)과 타겟(y) 변수 선택
features = df[['date_numeric']]  # 입력 변수: 날짜
target = df['population_count']  # 예측할 값: 유동인구 수

# 4. 모델 정의: RandomForestRegressor 모델 사용
# n_estimators=100: 100개의 결정 트리를 사용하여 예측의 정확성과 안정성을 높입니다.
# random_state=42: 코드를 다시 실행해도 항상 동일한 결과를 얻기 위한 시드 값입니다.
model = RandomForestRegressor(n_estimators=100, random_state=42)

# 5. 모델 학습: 'date_numeric'를 기반으로 'population_count'를 예측하도록 학습
model.fit(features, target)

# 6. 학습된 모델을 파일로 저장
# 'floating_population_model.pkl' 파일에 학습된 모델 객체를 저장하여
# 나중에 예측이 필요할 때 다시 학습할 필요 없이 불러와서 사용할 수 있습니다.
joblib.dump(model, 'floating_population_model.pkl')
print("AI 모델 학습 및 저장이 완료되었습니다: floating_population_model.pkl")