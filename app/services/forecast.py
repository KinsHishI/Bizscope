# app/services/forecast.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.schemas.finance import (
    FinancePoint,
    FinanceForecastAutoRequest,
    FinanceForecastAutoResponse,
    ForecastItem,
)
from app.db.crud import get_places_bbox
from app.db.session import AsyncSession
from app.db.crud import get_ftq_recent_near

from sklearn.ensemble import RandomForestRegressor


# ── 비용 가정치 ───────────────────────────────────────────────────────────────
@dataclass(slots=True)
class CostAssumptions:
    cogs_rate: float = 0.35
    labor_base: int = 3_200_000
    rent: int = 1_500_000
    utilities: int = 500_000
    marketing: int = 200_000


# ── 공통 유틸 ────────────────────────────────────────────────────────────────
def _assumption_dict(a_like) -> dict:
    if a_like is None:
        return {}
    if isinstance(a_like, dict):
        return a_like
    dump = getattr(a_like, "model_dump", None)
    return dump() if callable(dump) else dict(a_like)


def _to_month_index(series: Sequence[FinancePoint]) -> pd.Series:
    idx = pd.PeriodIndex([p.month for p in series], freq="M")
    vals = [p.sales for p in series]
    return pd.Series(vals, index=idx)


def _calc_costs(sales: int, a: CostAssumptions) -> dict:
    cogs = int(sales * a.cogs_rate)
    return {
        "cogs": cogs,
        "labor": a.labor_base,
        "rent": a.rent,
        "utilities": a.utilities,
        "marketing": a.marketing,
        "profit": sales - (cogs + a.labor_base + a.rent + a.utilities + a.marketing),
    }


def _make_items_with_conf(
    months: pd.PeriodIndex,
    mean: Iterable[float],
    lower: Iterable[float],
    upper: Iterable[float],
    a: CostAssumptions,
) -> list[ForecastItem]:
    out: list[ForecastItem] = []
    for m, mu, lo, hi in zip(months, mean, lower, upper):
        mu = max(0.0, float(mu))
        lo = max(0.0, float(lo))
        hi = max(0.0, float(hi))
        costs = _calc_costs(int(mu), a)
        out.append(
            ForecastItem(
                month=str(m), sales=int(mu), sales_pi=[int(lo), int(hi)], **costs
            )
        )
    return out


# ── 분기 내 월 가중치 & 랜덤 노이즈 ──────────────────────────────────────────
def _quarter_weights() -> list[float]:
    return [0.98, 1.00, 1.02]


def _apply_monthly_weights(start_period: pd.Period, h: int, base: Iterable[float]):
    months = pd.period_range(start=start_period, periods=h, freq="M")
    w = _quarter_weights()
    weights = np.array([w[(per.month - 1) % 3] for per in months], dtype=float)
    base = np.array(list(base), dtype=float)
    return base * weights, months


def _random_monthly_noise(h: int) -> np.ndarray:
    return np.random.default_rng().uniform(0.90, 1.10, size=h)


def _apply_monthly_noise(start_period: pd.Period, h: int, base: Iterable[float]):
    months = pd.period_range(start=start_period, periods=h, freq="M")
    noise = _random_monthly_noise(h)
    base = np.array(list(base), dtype=float)
    return base * noise, months


# ── ML 유틸 ──────────────────────────────────────────────────────────────────
def _make_features(y: pd.Series, exog: Optional[pd.Series]) -> pd.DataFrame:
    """
    y: 월 매출(PeriodIndex[M])
    exog: 월 단위 외생변수(유동인구) 시리즈(optional)
    """
    df = pd.DataFrame({"y": y.astype(float)})
    df["month"] = [idx.month for idx in y.index]
    df["quarter"] = [((idx.month - 1) // 3) + 1 for idx in y.index]
    df["exog"] = exog.reindex(y.index).astype(float) if exog is not None else 0.0
    df["lag1"] = df["y"].shift(1)
    df["lag2"] = df["y"].shift(2)
    df["lag3"] = df["y"].shift(3)
    return df


def _fit_ml_model(df: pd.DataFrame):
    feats = ["month", "quarter", "exog", "lag1", "lag2", "lag3"]
    train = df.dropna().copy()
    if len(train) < 6:
        return None, feats  # 데이터가 너무 적으면 ML 생략
    X = train[feats].values
    y = train["y"].values
    model = RandomForestRegressor(n_estimators=300, random_state=None)  # seed 없음
    model.fit(X, y)
    return model, feats


def _predict_ml_recursive(
    model,
    feats: list[str],
    y_hist: pd.Series,
    future_exog: Optional[pd.Series],
    horizon: int,
) -> np.ndarray:
    """마지막 3개월 y를 seed로 재귀 예측."""
    last_vals = list(map(float, y_hist.iloc[-3:].values))
    start = y_hist.index[-1] + 1
    months = pd.period_range(start=start, periods=horizon, freq="M")
    preds = []
    for i, per in enumerate(months):
        m = per.month
        q = ((m - 1) // 3) + 1
        ex = float(future_exog.iloc[i]) if future_exog is not None else 0.0
        lag1 = last_vals[-1] if len(last_vals) >= 1 else np.nan
        lag2 = last_vals[-2] if len(last_vals) >= 2 else np.nan
        lag3 = last_vals[-3] if len(last_vals) >= 3 else np.nan
        x = np.array([[m, q, ex, lag1, lag2, lag3]], dtype=float)
        y_hat = float(model.predict(x)[0])
        preds.append(y_hat)
        last_vals.append(y_hat)
        if len(last_vals) > 3:
            last_vals = last_vals[-3:]
    return np.array(preds, dtype=float)


# ── AUTO: 수성구 유동인구 → 월 분할(가중치) → 외생변수 결합 + 경량 ML 앙상블 ──
async def forecast_finance_auto(
    db: AsyncSession,
    req: FinanceForecastAutoRequest,
    *,
    lat: float | None,
    lon: float | None,
) -> FinanceForecastAutoResponse:
    """
    최근 n개월 매출 + (선택) lat/lon 근처의 '분기 유동인구'를
    월로 분할(0.98/1.00/1.02)하여 exog 구성.
    SARIMAX + (옵션)RandomForest를 0.6:0.4로 앙상블.
    출력단에 월별 랜덤 노이즈(0.90~1.10) 적용.
    """
    a = CostAssumptions(**_assumption_dict(req.assumptions))
    y = _to_month_index(req.series).asfreq("M")
    h = int(req.horizon_months)

    # ── 1) 외생변수(exog) 준비
    exog_hist: Optional[pd.Series] = None
    future_exog: Optional[pd.Series] = None
    base_quarter_pop: Optional[int] = None
    debug_reason: Optional[str] = None

    if lat is not None and lon is not None:
        # 1-1) 먼저 FTQ에서 최신 분기값 시도
        base_quarter_pop = await get_ftq_recent_near(db, lat, lon, deg=0.1)

        if base_quarter_pop is None:
            # 1-2) FTQ 없음 → Place.foot_traffic 로 폴백
            d = 0.002
            places = await get_places_bbox(db, lat - d, lon - d, lat + d, lon + d)
            foot_vals = [
                int(p.foot_traffic) for p in places if (p.foot_traffic or 0) > 0
            ]

            if foot_vals:
                base_quarter_pop = max(foot_vals)
                debug_reason = "FTQ 없음 → Place.foot_traffic로 대체"
            else:
                # 1-3) 그래도 없으면, 카페 수 기반 추정
                cafe_count = sum(
                    1 for p in places if (p.category or "").startswith("카페")
                )
                if cafe_count > 0:
                    base_quarter_pop = 8000 + 2000 * cafe_count
                    debug_reason = f"FTQ/Place 모두 없음 → 카페 {cafe_count}개로 추정"
                else:
                    debug_reason = "근방 FTQ/Place 데이터 모두 없음"

        # 1-4) exog 시계열 구성
        if base_quarter_pop and base_quarter_pop > 0:
            w = _quarter_weights()
            hist_vals = [
                base_quarter_pop * w[i % 3] / 3.0 for i, _ in enumerate(y.index)
            ]
            exog_hist = pd.Series(hist_vals, index=y.index)

            future_idx = pd.period_range(y.index[-1] + 1, periods=h, freq="M")
            fut_vals = [base_quarter_pop * w[i % 3] / 3.0 for i in range(h)]
            future_exog = pd.Series(fut_vals, index=future_idx)

    print(f"[auto] lat={lat}, lon={lon}")
    print(f"[auto] FTQ nearest(pop) -> {base_quarter_pop} (None=not found)")
    if "places" in locals():
        print(
            f"[auto] places within bbox: {len(places)}",
            f"foot>0: {sum(1 for p in places if (p.foot_traffic or 0) > 0)}",
            f"cafes: {sum(1 for p in places if (p.category or '').startswith('카페'))}",
        )
    print(f"[auto] exog_hist set? -> {exog_hist is not None}")

    # 2) SARIMAX 적합/예측
    if exog_hist is not None:
        model = SARIMAX(
            y,
            exog=exog_hist,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit(disp=False)
        fcast = fit.get_forecast(steps=h, exog=future_exog)
        model_name = "SARIMAX + exog(foot_traffic)"
        exog_coef = None
        try:
            for k, v in fit.params.items():
                if isinstance(k, str) and ("exog" in k or k.startswith("x")):
                    exog_coef = float(v)
                    break
        except Exception:
            exog_coef = None
    else:
        model = SARIMAX(
            y,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit(disp=False)
        fcast = fit.get_forecast(steps=h)
        model_name = "SARIMAX (no exog)"
        exog_coef = None

    mean_sarimax = fcast.predicted_mean.values
    ci = fcast.conf_int(alpha=0.05)
    lower_sarimax = ci.iloc[:, 0].values
    upper_sarimax = ci.iloc[:, 1].values

    # 3) 가벼운 ML 학습/예측
    mean_ens = mean_sarimax.copy()
    lower_ens = lower_sarimax.copy()
    upper_ens = upper_sarimax.copy()

    try:
        df_feats = _make_features(y, exog_hist)
        ml_model, ml_feats = _fit_ml_model(df_feats)
        if ml_model is not None:
            mean_ml = _predict_ml_recursive(
                ml_model, ml_feats, y_hist=y, future_exog=future_exog, horizon=h
            )
            alpha = 0.6  # SARIMAX 60%, ML 40%
            mean_ens = alpha * mean_sarimax + (1 - alpha) * mean_ml
            # CI는 SARIMAX를 기준으로 유지
            lower_ens = lower_sarimax * alpha
            upper_ens = upper_sarimax * alpha
            model_name += " + RF(0.4) ensemble"
    except Exception:
        pass

    # 4) 월별 가중치 + 랜덤 노이즈
    mean_w, months = _apply_monthly_weights(y.index[-1] + 1, h, mean_ens)
    noise = _random_monthly_noise(h)
    mean_noisy = mean_w * noise

    lower_w, _ = _apply_monthly_weights(y.index[-1] + 1, h, lower_ens)
    upper_w, _ = _apply_monthly_weights(y.index[-1] + 1, h, upper_ens)

    items = _make_items_with_conf(months, mean_noisy, lower_w, upper_w, a)

    # 5) Payback
    profits = np.array([it.profit for it in items], dtype=int)
    payback = (
        int(np.argmax(np.cumsum(profits) >= req.capex) + 1)
        if profits.sum() > 0
        else 999
    )

    # 6) 설명
    explain: list[str] = [
        f"원가율 {a.cogs_rate:.2f}, 인건비 base {a.labor_base:,}",
        "유동인구: 분기→월 분배 시 (0.98/1.00/1.02) 가중치 적용",
        "출력 예측치에 월별 랜덤 노이즈(0.90~1.10) 적용 — 호출마다 약간 다름",
    ]
    if base_quarter_pop:
        explain.append(f"주변 기준 분기 유동인구(최댓값) ≈ {base_quarter_pop:,}")
    if exog_hist is not None and exog_coef is not None and len(exog_hist):
        e0 = float(exog_hist.iloc[-1])
        delta_10pct = exog_coef * (0.10 * e0)
        explain.append(
            f"외생변수 계수 β≈{exog_coef:.4f} → exog 1단위↑ 시 매출 {exog_coef:.1f}↑ 추정"
        )
        explain.append(
            f"최근 exog 기준, 유동인구 +10% → 매출 약 +{int(delta_10pct):,}원 (선형 근사)"
        )
    if base_quarter_pop:
        explain.append(f"주변 기준 분기 유동인구(추정 기준값) ≈ {base_quarter_pop:,}")
    elif debug_reason:
        explain.append(f"exog 비활성화 사유: {debug_reason}")

    return FinanceForecastAutoResponse(
        forecast=items,
        payback_month=payback,
        payback_prob_12m=min(0.998, float((profits[:12] > 0).mean())),
        model=f"{model_name} + Monthly weights + Random noise",
        top_features=None,
        explain=explain,
    )
