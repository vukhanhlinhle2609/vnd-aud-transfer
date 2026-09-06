"""Validated multi-factor forecasts for Vietcombank's VND/AUD selling rate."""

from __future__ import annotations

import csv
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit


FACTOR_LABELS = {
    "aud_usd": "AUD/USD market rate",
    "broad_usd": "Broad US dollar",
    "usd_cny": "USD/CNY (China proxy)",
    "vix": "Global market volatility (VIX)",
    "brent_oil": "Brent oil",
    "us_10y": "US 10-year yield",
    "sp500": "Global equities (S&P 500)",
    "rba_cash_rate": "RBA cash rate",
    "au_10y": "Australian 10-year yield",
    "yield_spread": "Australia–US 10-year yield spread",
    "rba_aud_usd": "RBA AUD/USD reference rate",
    "rba_aud_twi": "RBA AUD trade-weighted index",
    "rba_aud_cny": "RBA AUD/CNY reference rate",
    "rba_aud_vnd": "RBA AUD/VND reference rate",
    "rba_aud_jpy": "RBA AUD/JPY reference rate",
    "rba_aud_eur": "RBA AUD/EUR reference rate",
}

MODEL_LABELS = {
    "ridge": "Regularised multi-factor trend",
    "elastic": "Sparse multi-factor trend",
    "gradient": "Gradient-boosted factor model",
    "hist_gradient": "Robust boosted factor model",
    "extra_trees": "Non-linear factor ensemble",
    "fair_value": "RBA fair-value convergence model",
}


def _load_rates(path: Path) -> pd.Series:
    rows: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("date") and row.get("sell"):
                rows[row["date"][:10]] = float(row["sell"])
    series = pd.Series(rows, dtype=float)
    series.index = pd.to_datetime(series.index)
    return series.sort_index().rename("rate")


def _load_factors(path: Path, dates: pd.DatetimeIndex) -> pd.DataFrame:
    factors = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    factors = factors.apply(pd.to_numeric, errors="coerce").sort_index()
    aligned_raw = factors.reindex(dates, method="ffill")
    aligned = pd.DataFrame(index=dates)
    for column in aligned_raw:
        if column.startswith("rba_aud_") or column == "rba_cash_rate":
            # These RBA series are published before the final UTC-dated VCB
            # collection used in the daily file.
            aligned[column] = aligned_raw[column]
        elif column == "au_10y":
            # The RBA government-yield table is released weekly with a lag.
            aligned[column] = aligned_raw[column].shift(3)
        else:
            # U.S. and FRED markets close after Vietcombank's daytime quote.
            aligned[column] = aligned_raw[column].shift(1)
    aligned["yield_spread"] = aligned["au_10y"] - aligned["us_10y"]
    return aligned


def _build_features(rates: pd.Series, factors: pd.DataFrame) -> pd.DataFrame:
    features = pd.DataFrame(index=rates.index)
    features["rate_level"] = rates

    for lag in (1, 2, 3, 5, 7, 14, 30):
        features[f"rate_change_{lag}d"] = rates.diff(lag)
        features[f"rate_return_{lag}d"] = rates.pct_change(lag)

    daily_change = rates.diff()
    for window in (3, 7, 14, 30, 60):
        rolling = rates.rolling(window, min_periods=max(2, window // 2))
        features[f"rate_vs_ma_{window}d"] = rates / rolling.mean() - 1
        features[f"rate_volatility_{window}d"] = daily_change.rolling(
            window, min_periods=max(2, window // 2)
        ).std()

    for window in (7, 30):
        rolling_min = rates.rolling(window, min_periods=max(2, window // 2)).min()
        rolling_max = rates.rolling(window, min_periods=max(2, window // 2)).max()
        denominator = (rolling_max - rolling_min).replace(0, np.nan)
        features[f"rate_range_position_{window}d"] = (
            rates - rolling_min
        ) / denominator

    if "rba_aud_vnd" in factors:
        market_spread = rates - factors["rba_aud_vnd"]
        features["vcb_markup_vs_rba"] = market_spread
        for window in (5, 10, 20, 60):
            normal_markup = market_spread.rolling(
                window, min_periods=max(3, window // 2)
            ).median().shift(1)
            implied_fair_value = factors["rba_aud_vnd"] + normal_markup
            features[f"rba_fair_value_gap_{window}d"] = (
                implied_fair_value - rates
            )

    day_of_week = rates.index.dayofweek
    features["weekday_sin"] = np.sin(2 * np.pi * day_of_week / 7)
    features["weekday_cos"] = np.cos(2 * np.pi * day_of_week / 7)
    features["is_weekend"] = (day_of_week >= 5).astype(float)

    factor_features: dict[str, pd.Series] = {}
    for factor_name in factors.columns:
        factor = factors[factor_name]
        factor_features[f"{factor_name}_level"] = factor
        for lag in (1, 3, 5, 10, 20):
            factor_features[f"{factor_name}_change_{lag}d"] = factor.pct_change(
                lag, fill_method=None
            )
        factor_mean = factor.rolling(20, min_periods=10).mean()
        factor_std = factor.rolling(20, min_periods=10).std()
        factor_features[f"{factor_name}_zscore_20d"] = (
            factor - factor_mean
        ) / factor_std.replace(0, np.nan)

    features = pd.concat(
        [features, pd.DataFrame(factor_features, index=rates.index)],
        axis=1,
    )
    return features.replace([np.inf, -np.inf], np.nan)


def _candidate_models() -> list[tuple[str, object, int | None]]:
    return [
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                SelectKBest(f_regression, k=20),
                Ridge(alpha=10.0),
            ),
            180,
        ),
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                SelectKBest(f_regression, k=40),
                Ridge(alpha=50.0),
            ),
            180,
        ),
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                SelectKBest(f_regression, k=20),
                Ridge(alpha=300.0),
            ),
            180,
        ),
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                SelectKBest(f_regression, k=20),
                Ridge(alpha=1000.0),
            ),
            180,
        ),
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                Ridge(alpha=100.0),
            ),
            None,
        ),
        (
            "fair_value",
            make_pipeline(
                ColumnTransformer(
                    [("fair_value", "passthrough", ["rba_fair_value_gap_5d"])]
                ),
                SimpleImputer(strategy="median"),
                Ridge(alpha=100.0),
            ),
            180,
        ),
        (
            "fair_value",
            make_pipeline(
                ColumnTransformer(
                    [("fair_value", "passthrough", ["rba_fair_value_gap_20d"])]
                ),
                SimpleImputer(strategy="median"),
                Ridge(alpha=100.0),
            ),
            180,
        ),
        (
            "fair_value",
            make_pipeline(
                ColumnTransformer(
                    [("fair_value", "passthrough", ["rba_fair_value_gap_60d"])]
                ),
                SimpleImputer(strategy="median"),
                Ridge(alpha=100.0),
            ),
            180,
        ),
        (
            "ridge",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                Ridge(alpha=500.0),
            ),
            None,
        ),
        (
            "elastic",
            make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                ElasticNet(alpha=2.0, l1_ratio=0.15, max_iter=5000),
            ),
            None,
        ),
        (
            "gradient",
            make_pipeline(
                SimpleImputer(strategy="median"),
                GradientBoostingRegressor(
                    loss="huber",
                    learning_rate=0.035,
                    n_estimators=180,
                    max_depth=2,
                    min_samples_leaf=12,
                    random_state=42,
                ),
            ),
            180,
        ),
        (
            "hist_gradient",
            make_pipeline(
                SimpleImputer(strategy="median"),
                HistGradientBoostingRegressor(
                    loss="absolute_error",
                    learning_rate=0.045,
                    max_iter=220,
                    max_leaf_nodes=9,
                    min_samples_leaf=16,
                    l2_regularization=12.0,
                    random_state=42,
                ),
            ),
            180,
        ),
        (
            "extra_trees",
            make_pipeline(
                SimpleImputer(strategy="median"),
                ExtraTreesRegressor(
                    n_estimators=180,
                    max_depth=7,
                    min_samples_leaf=7,
                    max_features=0.65,
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
            180,
        ),
    ]


def _tune_model(
    x: pd.DataFrame,
    y: pd.Series,
    horizon: int,
    evaluation_count: int,
) -> tuple[str, object, float, float, int | None]:
    tune_end = len(x) - evaluation_count
    tune_x = x.iloc[:tune_end]
    tune_y = y.iloc[:tune_end]
    test_size = max(14, min(28, len(tune_x) // 8))
    splitter = TimeSeriesSplit(n_splits=4, test_size=test_size, gap=horizon)
    scales = (0.25, 0.5, 0.75, 1.0, 1.25)

    best: tuple[float, str, object, float, int | None] | None = None
    for model_id, template, training_window in _candidate_models():
        actual: list[float] = []
        raw_predictions: list[float] = []
        for train_indices, test_indices in splitter.split(tune_x):
            if training_window is not None:
                train_indices = train_indices[-training_window:]
            model = clone(template)
            model.fit(tune_x.iloc[train_indices], tune_y.iloc[train_indices])
            raw_predictions.extend(model.predict(tune_x.iloc[test_indices]))
            actual.extend(tune_y.iloc[test_indices])

        for scale in scales:
            scaled = np.asarray(raw_predictions) * scale
            score = mean_absolute_error(actual, scaled)
            candidate = (score, model_id, template, scale, training_window)
            if best is None or candidate[0] < best[0]:
                best = candidate

    assert best is not None
    _, model_id, template, scale, training_window = best
    return model_id, template, scale, best[0], training_window


def _walk_forward_evaluation(
    x: pd.DataFrame,
    y: pd.Series,
    horizon: int,
    template: object,
    scale: float,
    evaluation_count: int,
    training_window: int | None,
) -> tuple[np.ndarray, np.ndarray]:
    start = len(x) - evaluation_count
    predictions: list[float] = []
    actual: list[float] = []

    # Refit at each origin. The training gap ensures every target used by the
    # model would already have been observed at that historical forecast time.
    for origin in range(start, len(x)):
        train_end = origin - horizon + 1
        train_start = (
            max(0, train_end - training_window)
            if training_window is not None
            else 0
        )
        model = clone(template)
        model.fit(x.iloc[train_start:train_end], y.iloc[train_start:train_end])
        predictions.append(float(model.predict(x.iloc[[origin]])[0]) * scale)
        actual.append(float(y.iloc[origin]))
    return np.asarray(predictions), np.asarray(actual)


def _local_drivers(
    model: object,
    latest_x: pd.DataFrame,
    training_x: pd.DataFrame,
    scale: float,
    limit: int = 6,
) -> list[dict[str, float | str]]:
    baseline_prediction = float(model.predict(latest_x)[0]) * scale
    medians = training_x.median(numeric_only=True)
    drivers: list[dict[str, float | str]] = []
    for column in latest_x.columns:
        comparison = latest_x.copy()
        median = medians.get(column, np.nan)
        if pd.isna(median):
            continue
        comparison.loc[:, column] = median
        impact = baseline_prediction - float(model.predict(comparison)[0]) * scale
        if abs(impact) < 0.005:
            continue
        if column.startswith("rba_fair_value_gap"):
            label = "RBA AUD/VND fair-value gap"
        elif column.startswith("rate_"):
            label = "Vietcombank rate trend"
        else:
            root_name = next(
                (name for name in FACTOR_LABELS if column.startswith(f"{name}_")),
                None,
            )
            label = (
                FACTOR_LABELS[root_name]
                if root_name is not None
                else "Calendar pattern"
            )
        drivers.append(
            {
                "feature": column,
                "label": label,
                "impact": impact,
            }
        )

    drivers.sort(key=lambda item: abs(float(item["impact"])), reverse=True)
    unique: list[dict[str, float | str]] = []
    seen_labels: set[str] = set()
    for driver in drivers:
        label = str(driver["label"])
        if label in seen_labels:
            continue
        seen_labels.add(label)
        unique.append(driver)
        if len(unique) == limit:
            break
    return unique


def _factor_snapshot(path: Path) -> list[dict[str, float | str]]:
    factors = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    factors = factors.apply(pd.to_numeric, errors="coerce").sort_index()
    snapshots: list[dict[str, float | str]] = []
    for name in FACTOR_LABELS:
        if name not in factors:
            continue
        available = factors[name].dropna()
        if available.empty:
            continue
        latest_value = float(available.iloc[-1])
        previous_value = float(available.iloc[max(0, len(available) - 6)])
        change = (
            (latest_value / previous_value - 1) * 100
            if previous_value
            else 0.0
        )
        snapshots.append(
            {
                "key": name,
                "label": FACTOR_LABELS[name],
                "value": latest_value,
                "change_5d": change,
                "date": available.index[-1].date().isoformat(),
            }
        )
    return snapshots


def build_forecast(
    rate_path: Path,
    factor_path: Path,
    horizons: int = 7,
) -> dict[str, object]:
    rates = _load_rates(rate_path)
    factors = _load_factors(factor_path, rates.index)
    features = _build_features(rates, factors)
    forecasts: list[dict[str, object]] = []
    drivers_by_horizon: dict[int, list[dict[str, float | str]]] = {}

    for horizon in range(1, horizons + 1):
        target_delta = rates.shift(-horizon) - rates
        x = features.iloc[:-horizon]
        y = target_delta.iloc[:-horizon]
        evaluation_count = min(60, max(35, len(x) // 5))
        model_id, template, scale, tuning_mae, training_window = _tune_model(
            x, y, horizon, evaluation_count
        )
        evaluation_predictions, evaluation_actual = _walk_forward_evaluation(
            x,
            y,
            horizon,
            template,
            scale,
            evaluation_count,
            training_window,
        )
        model_mae = mean_absolute_error(
            evaluation_actual, evaluation_predictions
        )
        baseline_mae = mean_absolute_error(
            evaluation_actual, np.zeros_like(evaluation_actual)
        )
        residuals = np.abs(evaluation_actual - evaluation_predictions)
        signed_residuals = evaluation_actual - evaluation_predictions
        interval_radius = float(np.quantile(residuals, 0.80))
        interval_coverage = float(
            np.mean(residuals <= interval_radius) * 100
        )
        tolerance_accuracy = float(
            np.mean(
                residuals
                / rates.iloc[-evaluation_count - horizon:-horizon].to_numpy()
                <= 0.005
            )
            * 100
        )

        final_model = clone(template)
        final_start = (
            max(0, len(x) - training_window)
            if training_window is not None
            else 0
        )
        final_model.fit(x.iloc[final_start:], y.iloc[final_start:])
        predicted_delta = float(
            final_model.predict(features.iloc[[-1]])[0]
        ) * scale
        estimate = float(rates.iloc[-1] + predicted_delta)

        if horizon in (1, horizons):
            drivers_by_horizon[horizon] = _local_drivers(
                final_model,
                features.iloc[[-1]],
                x.iloc[final_start:],
                scale,
            )

        forecasts.append(
            {
                "horizon": horizon,
                "date": rates.index[-1].date() + timedelta(days=horizon),
                "estimate": estimate,
                "change": predicted_delta,
                "change_pct": predicted_delta / rates.iloc[-1] * 100,
                "low": estimate - interval_radius,
                "high": estimate + interval_radius,
                "mae": float(model_mae),
                "baseline_mae": float(baseline_mae),
                "improvement_pct": float(
                    (baseline_mae - model_mae) / baseline_mae * 100
                    if baseline_mae
                    else 0.0
                ),
                "interval_coverage": interval_coverage,
                "tolerance_accuracy": tolerance_accuracy,
                "backtest_count": evaluation_count,
                "model_id": model_id,
                "model_name": MODEL_LABELS[model_id],
                "scale": scale,
                "tuning_mae": float(tuning_mae),
                "training_window": training_window,
                "probability_lower": float(
                    np.mean(predicted_delta + signed_residuals < 0) * 100
                ),
                "probability_higher": float(
                    np.mean(predicted_delta + signed_residuals > 0) * 100
                ),
                "beats_baseline": bool(model_mae < baseline_mae),
            }
        )

    return {
        "latest_rate": float(rates.iloc[-1]),
        "latest_date": rates.index[-1].date(),
        "forecasts": forecasts,
        "drivers": drivers_by_horizon,
        "factor_snapshot": _factor_snapshot(factor_path),
        "factor_count": len(factors.columns),
        "feature_count": len(features.columns),
        "data_start": rates.index[0].date(),
        "data_count": len(rates),
    }


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    result = build_forecast(
        project_root / "data" / "vcb_aud_daily.csv",
        project_root / "data" / "market_factors.csv",
    )
    output_path = project_root / "data" / "forecast_output.json"
    output_path.write_text(
        json.dumps(result, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        "day  estimate  change   model MAE  baseline  improvement  model"
    )
    for forecast in result["forecasts"]:
        print(
            f"{forecast['horizon']:>3}  {forecast['estimate']:>8.2f}  "
            f"{forecast['change']:>+7.2f}  {forecast['mae']:>9.2f}  "
            f"{forecast['baseline_mae']:>8.2f}  "
            f"{forecast['improvement_pct']:>+10.2f}%  "
            f"{forecast['model_name']}"
        )
    print(f"Saved validated forecast to {output_path}")
