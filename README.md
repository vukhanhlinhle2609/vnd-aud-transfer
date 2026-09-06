# VND to AUD Transfer Optimiser

This project collects Vietcombank's AUD selling rate and provides a bilingual,
mobile-friendly transfer-planning dashboard.

## Forecasting

The automated forecast pipeline combines the Vietcombank history with:

- RBA AUD/VND, AUD/USD, AUD/CNY, AUD/JPY, AUD/EUR and trade-weighted rates;
- Australian and US interest rates and 10-year yields;
- broad US-dollar strength, VIX, Brent oil and the S&P 500; and
- lagged rate trends, volatility, calendar effects and the gap between the
  Vietcombank quote and the RBA reference rate.

Separate models are selected for horizons one through seven. Candidate
regularised linear, boosted-tree, non-linear ensemble and RBA fair-value
models are tuned on older time splits and checked using walk-forward tests.
The dashboard always compares them with the repeat-current-rate baseline and
shows when the additional complexity did not improve accuracy.

The scheduled GitHub workflow refreshes the rate and market factors, reruns
validation, and writes `data/forecast_output.json` every six hours. Streamlit
only reads the precomputed result, so the public dashboard remains responsive
on phones and laptops.
