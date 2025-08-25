# 📈 BIZSCOPE: AI 기반 상권 분석 솔루션

## 🧐 프로젝트 소개

**BIZSCOPE**는 대구 지역, 특히 창업과 폐업이 잦은 수성구를 중심으로 예비 창업자들의 성공적인 카페 창업을 돕기 위해 개발된 AI 기반 상권 분석 서비스입니다.
사용자가 지정한 위치를 기준으로 상권 데이터를 수집·분석하여 창업 적합도 점수(0~100점) 로 제공하고, 데이터 기반 의사결정을 지원합니다.

---

## ✨ 주요 기능

* **실시간 경쟁 분석**: 카카오맵 API를 활용하여 반경 2km 내 모든 경쟁업체 정보를 수집하고, 프랜차이즈와 개인 카페 비율을 분석합니다.
* **유동인구 분석**: 대구 수성구 공공데이터를 활용하여, 상권 및 주간 유동인구 데이터를 분석에 반영합니다.
* **AI 기반 예측**: 과거 유동인구 데이터를 학습한 AI 모델을 통해 현재 시점의 유동인구를 예측하여 분석의 정확도를 높입니다.
* **창업 적합도 점수 제공**: 경쟁 강도, 유동인구 등 핵심 지표를 종합하여 해당 위치의 창업 적합도를 0점에서 100점 사이의 직관적인 점수로 제공합니다.

---

## 🛠️ 기술 스택

* **Backend**: Python, FastAPI
* **Data Handling**: Pandas, Scikit-learn
* **Database**: SQLite
* **Infra**: Uvicorn

---

## 🚀 실행 방법

1.  **프로젝트 클론 및 가상환경 설정**
    ```bash
    git clone <레포지토리_주소>
    cd BizScope
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

3.  **.env 파일 설정**
    * 프로젝트 최상위 폴더에 `.env` 파일을 생성하고 아래 내용을 채워주세요.
    ```env
    SUSEONG_API_KEY=발급받은_공공데이터_API_서비스키
    KAKAO_API_KEY=발급받은_카카오맵_API_서비스키
    ```

4.  **데이터 준비 및 AI 모델 학습**
    ```bash
    # DB 테이블 생성
    python3 core/db/database.py
    
    # 공공데이터 수집 (시간이 다소 소요될 수 있습니다)
    python3 data_ingestion.py
    
    # AI 모델 학습
    python3 train_model.py
    ```

5.  **서버 실행**
    ```bash
    uvicorn main:app --reload
    ```
    * 서버 실행 후 `http://127.0.0.1:8000`으로 접속

---

## 📖 API 명세

### 1️⃣ 헬스체크
* **Endpoint**: GET /health
* **설명**: 서버 상태 확인용
* **Success Response (200 OK)**:
    ```json
    { "status": "ok" }
    ```

### 2️⃣ 상권 분석

* **Endpoint**: `POST /analysis/area`
* **설명**: 지정 좌표 반경 내 카페 상권을 분석하여 창업 적합도를 점수화
* **Request Body**:
    ```json
    {
      "lat": 35.8427,
     "lon": 128.627,
    "radius_m": 2000
    }
    ```
* **Success Response (200 OK)**:
    ```json
    {
      "suitability_score": 75,
      "reasoning": {
        "competitor_count": 45,
        "franchise_count": 9,
        "personal_count": 36,
        "floating_population": 46963,
        "radius_km": 2
      },
      "competitor_analysis": {
        "count": 45,
        "types": {
          "franchise": 9,
          "personal": 36
        },
        "avg_rating": 4.0
      }
    }
    ```

### 3️⃣ 재무/매출 예측 (AI 기반)

* **Endpoint**: `POST /finance/forecast_auto`
* **설명**: 과거 매출 데이터 + (옵션) 위치 기반 유동인구 데이터를 활용해 향후 N개월 매출/비용/이익 예측
* **Request Body**:
    ```json
    {
        "series": [
            { "month": "2024-10", "sales": 12000000 },
            { "month": "2024-11", "sales": 12500000 },
            { "month": "2024-12", "sales": 13000000 },
            { "month": "2025-01", "sales": 14000000 }
          ],
        "horizon_months": 6,
        "capex": 50000000,
        "lat": 35.856,
        "lon": 128.622
    }
    ```
* **Success Response (200 OK)**:
    ```json
    {
        "forecast": [
            {
                "month": "2025-04",
                "sales": 14072364,
                "sales_pi": [13227283, 13232716],
                "cogs": 4925327,
                "labor": 3200000,
                "rent": 1500000,
                "utilities": 500000,
                "marketing": 200000,
                "profit": 3747037
            },
        ...
        ],
        "payback_month": 6,
        "payback_prob_12m": 0.998,
        "model": "SARIMAX + exog(foot_traffic) + Monthly weights + Random noise",
        "top_features": null,
        "explain": [
            "원가율 0.35, 인건비 base 3,200,000",
            "유동인구: 분기→월 분배 시 (0.98/1.00/1.02) 가중치 적용",
            "출력 예측치에 월별 랜덤 노이즈(0.90~1.10) 적용",
            "주변 기준 분기 유동인구(최댓값) ≈ 12,000"
        ]
    }
    ```
