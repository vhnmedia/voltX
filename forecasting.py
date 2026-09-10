"""
GreenWatt — ML Forecasting Service
Two separate models:
  1. PRICE FORECASTING: XGBoost regressor → next day's 96 DAM block MCPs
     + 10th/90th percentile quantile regression for confidence band.
  2. LOAD FORECASTING: LightGBM regressor → facility consumption per block.

ACCURACY CAVEAT (from README):
A weekend-built price model will typically land at 15–20% MAPE.
Present forecasts as directional guidance for identifying relatively cheap
windows — not a guaranteed price prediction. Always display confidence bands.
"""
import logging
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PriceForecastBlock:
    """
    Single block price forecast with mandatory uncertainty bounds.
    Never output a single falsely-precise number — always return all three.
    """
    block_id: int
    timestamp: str
    predicted_price: float
    lower_bound: float   # 10th percentile
    upper_bound: float   # 90th percentile
    market_type: str = "DAM"


@dataclass
class LoadForecastBlock:
    block_id: int
    timestamp: str
    predicted_kw: float
    facility_id: str


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def build_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives lagged & rolling features from market_prices data.
    Features:
      - same_block_yesterday: price for this block 24h ago
      - same_block_last_week: price for this block 7d ago
      - rolling_7d_avg: 7-day rolling average price
      - day_of_week: 0=Mon, 6=Sun
      - is_holiday: boolean (simplified; use indian-holidays lib in production)
      - hour_of_day, block_in_day
      - solar_proxy: estimated solar generation (from weather if available)
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    df["hour_of_day"] = df["timestamp"].dt.hour
    df["block_in_day"] = df["block_id"]
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["month"] = df["timestamp"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Lag features (requires historical data; filled with median on first run)
    df["lag_96"] = df["mcp_price"].shift(96)    # same block yesterday (96 blocks/day)
    df["lag_672"] = df["mcp_price"].shift(672)  # same block last week
    df["rolling_7d_avg"] = df["mcp_price"].rolling(672, min_periods=10).mean()
    df["rolling_24h_avg"] = df["mcp_price"].rolling(96, min_periods=10).mean()

    # Solar proxy: midday blocks (block 25-52, 6am-1pm) get solar indicator
    df["solar_hour"] = (
        ((df["block_in_day"] >= 25) & (df["block_in_day"] <= 52)).astype(int)
    )

    # Holiday stub (simplified — plug in 'holidays' library for production)
    df["is_holiday"] = 0

    df = df.fillna(df.median(numeric_only=True))
    return df


PRICE_FEATURE_COLS = [
    "hour_of_day", "block_in_day", "day_of_week", "month",
    "is_weekend", "lag_96", "lag_672", "rolling_7d_avg", "rolling_24h_avg",
    "solar_hour", "is_holiday"
]

LOAD_FEATURE_COLS = [
    "hour_of_day", "block_in_day", "day_of_week", "month",
    "is_weekend", "lag_96", "lag_672", "rolling_7d_avg",
    "is_holiday", "temperature", "solar_irradiance"
]


# ─────────────────────────────────────────────────────────────────────────────
# PRICE FORECAST MODEL
# ─────────────────────────────────────────────────────────────────────────────

class PriceForecastModel:
    """
    XGBoost regressor for point forecast + quantile regression for bounds.
    In production: load a pre-trained model from Supabase Storage / model registry.
    For hackathon: trains on the simulated data in memory.
    """

    def __init__(self):
        self.model_point = None
        self.model_q10 = None
        self.model_q90 = None
        self.is_trained = False
        self._init_models()

    def _init_models(self):
        try:
            from xgboost import XGBRegressor
            self.model_point = XGBRegressor(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8, random_state=42,
                n_jobs=-1
            )
            # Quantile regression via sklearn GradientBoostingRegressor
            from sklearn.ensemble import GradientBoostingRegressor
            self.model_q10 = GradientBoostingRegressor(
                loss="quantile", alpha=0.10, n_estimators=200,
                max_depth=4, learning_rate=0.05, random_state=42
            )
            self.model_q90 = GradientBoostingRegressor(
                loss="quantile", alpha=0.90, n_estimators=200,
                max_depth=4, learning_rate=0.05, random_state=42
            )
            logger.info("[PriceForecast] Models initialised")
        except ImportError as e:
            logger.warning(f"[PriceForecast] ML libraries not available: {e}. Using statistical fallback.")

    def train(self, df: pd.DataFrame):
        """Train all three models on historical price data."""
        if self.model_point is None:
            logger.warning("[PriceForecast] Training skipped — models not initialised")
            return

        df_feat = build_price_features(df)
        X = df_feat[PRICE_FEATURE_COLS].values
        y = df_feat["mcp_price"].values

        if len(X) < 200:
            logger.warning("[PriceForecast] Insufficient training data (<200 rows)")
            return

        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        self.model_point.fit(X_train, y_train)
        self.model_q10.fit(X_train, y_train)
        self.model_q90.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate
        y_pred = self.model_point.predict(X_test)
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100
        directional = np.mean(
            np.sign(y_test - y_test.mean()) == np.sign(y_pred - y_pred.mean())
        ) * 100
        logger.info(f"[PriceForecast] Test MAPE={mape:.1f}%, Directional={directional:.1f}%")
        return {"mape": round(mape, 2), "directional_accuracy": round(directional, 2)}

    def predict(self, features_df: pd.DataFrame) -> List[PriceForecastBlock]:
        """
        Predict prices for upcoming blocks.
        If model not trained, falls back to statistical simulation.
        """
        import math

        if not self.is_trained or self.model_point is None:
            return self._statistical_fallback(features_df)

        df_feat = build_price_features(features_df)
        X = df_feat[PRICE_FEATURE_COLS].values

        point = self.model_point.predict(X)
        q10 = self.model_q10.predict(X)
        q90 = self.model_q90.predict(X)

        results = []
        for i, row in df_feat.iterrows():
            idx = df_feat.index.get_loc(i)
            results.append(PriceForecastBlock(
                block_id=int(row["block_in_day"]),
                timestamp=str(row["timestamp"]),
                predicted_price=round(max(1.0, float(point[idx])), 4),
                lower_bound=round(max(0.5, float(q10[idx])), 4),
                upper_bound=round(max(1.0, float(q90[idx])), 4),
            ))
        return results

    def _statistical_fallback(self, features_df: pd.DataFrame) -> List[PriceForecastBlock]:
        """
        When model isn't trained yet: use a statistical model based on
        typical India IEX price patterns. Provides reasonable directional guidance.
        """
        results = []
        for _, row in features_df.iterrows():
            block = int(row.get("block_id", row.get("block_in_day", 1)))
            hour = (block - 1) * 0.25
            import math
            morning = 4 * math.exp(-0.5 * ((hour - 10) / 2) ** 2)
            evening = 5.5 * math.exp(-0.5 * ((hour - 20) / 1.5) ** 2)
            base = 3.0 + morning + evening
            noise = np.random.normal(0, 0.2)
            predicted = max(1.5, round(base + noise, 4))
            spread = predicted * 0.25  # 25% uncertainty band
            results.append(PriceForecastBlock(
                block_id=block,
                timestamp=str(row.get("timestamp", "")),
                predicted_price=predicted,
                lower_bound=round(max(0.5, predicted - spread), 4),
                upper_bound=round(predicted + spread, 4),
            ))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# LOAD FORECAST MODEL
# ─────────────────────────────────────────────────────────────────────────────

class LoadForecastModel:
    """
    LightGBM regressor predicting facility consumption per 15-min block.
    Evaluated with MAPE per facility.
    """

    def __init__(self):
        self.models: Dict[str, Any] = {}  # facility_id → trained model
        self._lgbm_available = False
        try:
            import lightgbm  # noqa
            self._lgbm_available = True
        except ImportError:
            logger.warning("[LoadForecast] LightGBM not available. Using statistical fallback.")

    def train_for_facility(self, facility_id: str, df: pd.DataFrame) -> Dict:
        """Train a facility-specific load model."""
        if not self._lgbm_available:
            logger.warning(f"[LoadForecast] Skipping training for {facility_id}")
            return {}

        import lightgbm as lgb

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["block_in_day"] = ((df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute) // 15) + 1
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["month"] = df["timestamp"].dt.month
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["lag_96"] = df["consumption_kw"].shift(96)
        df["lag_672"] = df["consumption_kw"].shift(672)
        df["rolling_7d_avg"] = df["consumption_kw"].rolling(672, min_periods=20).mean()
        df["is_holiday"] = 0
        df = df.fillna(df.median(numeric_only=True))

        feature_cols = ["hour_of_day", "block_in_day", "day_of_week", "month",
                        "is_weekend", "lag_96", "lag_672", "rolling_7d_avg", "is_holiday"]
        X = df[feature_cols].values
        y = df["consumption_kw"].values

        if len(X) < 200:
            return {"error": "Insufficient data"}

        split = int(len(X) * 0.8)
        model = lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.05,
                                   random_state=42, n_jobs=-1, verbose=-1)
        model.fit(X[:split], y[:split])
        self.models[facility_id] = (model, feature_cols)

        y_pred = model.predict(X[split:])
        mape = np.mean(np.abs((y[split:] - y_pred) / (y[split:] + 1e-8))) * 100
        logger.info(f"[LoadForecast] Facility {facility_id}: MAPE={mape:.1f}%")
        return {"facility_id": facility_id, "mape": round(mape, 2)}

    def predict(self, facility_id: str, forecast_date: date) -> List[LoadForecastBlock]:
        """Predict 96 blocks for a facility on forecast_date."""
        base_dt = datetime.combine(forecast_date, datetime.min.time())
        rows = []
        for block in range(1, 97):
            ts = base_dt + timedelta(minutes=15 * (block - 1))
            rows.append({
                "timestamp": ts,
                "block_id": block,
                "hour_of_day": ts.hour,
                "block_in_day": block,
                "day_of_week": ts.weekday(),
                "month": ts.month,
                "is_weekend": int(ts.weekday() >= 5),
                "lag_96": 0, "lag_672": 0, "rolling_7d_avg": 500,
                "is_holiday": 0,
            })
        df = pd.DataFrame(rows)

        if facility_id in self.models:
            model, feature_cols = self.models[facility_id]
            X = df[feature_cols].values
            preds = model.predict(X)
        else:
            # Statistical fallback
            import math
            preds = []
            for _, row in df.iterrows():
                hour = row["hour_of_day"] + (row["block_id"] % 4) * 0.25
                work = max(0, math.sin(math.pi * (hour - 8) / 10)) if 8 <= hour <= 20 else 0.1
                preds.append(max(50, 600 * (0.3 + 0.7 * work) + np.random.normal(0, 30)))

        return [
            LoadForecastBlock(
                block_id=int(df.iloc[i]["block_id"]),
                timestamp=str(df.iloc[i]["timestamp"]),
                predicted_kw=round(max(0, float(preds[i])), 2),
                facility_id=facility_id,
            )
            for i in range(len(df))
        ]


# Singleton instances (initialised at startup)
_price_model: Optional[PriceForecastModel] = None
_load_model: Optional[LoadForecastModel] = None


def get_price_model() -> PriceForecastModel:
    global _price_model
    if _price_model is None:
        _price_model = PriceForecastModel()
    return _price_model


def get_load_model() -> LoadForecastModel:
    global _load_model
    if _load_model is None:
        _load_model = LoadForecastModel()
    return _load_model
