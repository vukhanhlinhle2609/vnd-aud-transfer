# Backtest of the discarded historical percentile timing strategy.
import csv
from pathlib import Path
from statistics import mean


HISTORY_DAYS = 30
TRANSFER_WINDOW_DAYS = 14
TRANSFER_AMOUNT_AUD = 3000

data_file = (
    Path(__file__).parent.parent
    / "data"
    / "vcb_aud_daily.csv"
)

with data_file.open(newline="", encoding="utf-8") as file:
    rows = [
        row
        for row in csv.DictReader(file)
        if row.get("date") and row.get("sell")
    ]

rows.sort(key=lambda row: row["date"])

dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]

minimum_rows = HISTORY_DAYS + TRANSFER_WINDOW_DAYS + 1

if len(rates) < minimum_rows:
    raise ValueError(
        f"At least {minimum_rows} days of data are required."
    )

baseline_results = []
strategy_results = []

for start_index in range(
    HISTORY_DAYS,
    len(rates) - TRANSFER_WINDOW_DAYS,
):
    deadline_index = start_index + TRANSFER_WINDOW_DAYS

    baseline_rate = rates[start_index]
    baseline_results.append(baseline_rate)

    remaining_fraction = 1.0
    strategy_cost_per_aud = 0.0
    split_used = False

    for day_index in range(
        start_index,
        deadline_index + 1,
    ):
        current_rate = rates[day_index]
        days_remaining = deadline_index - day_index

        historical_rates = sorted(
            rates[
                day_index - HISTORY_DAYS:
                day_index
            ]
        )

        cheap_cutoff = historical_rates[
            int((len(historical_rates) - 1) * 0.25)
        ]

        expensive_cutoff = historical_rates[
            int((len(historical_rates) - 1) * 0.75)
        ]

        if days_remaining <= 2:
            strategy_cost_per_aud += (
                remaining_fraction * current_rate
            )
            remaining_fraction = 0
            break

        if current_rate <= cheap_cutoff:
            strategy_cost_per_aud += (
                remaining_fraction * current_rate
            )
            remaining_fraction = 0
            break

        if (
            current_rate >= expensive_cutoff
            and days_remaining >= 8
        ):
            continue

        if not split_used:
            transfer_fraction = 0.5
            strategy_cost_per_aud += (
                transfer_fraction * current_rate
            )
            remaining_fraction -= transfer_fraction
            split_used = True

    if remaining_fraction > 0:
        strategy_cost_per_aud += (
            remaining_fraction * rates[deadline_index]
        )

    strategy_results.append(strategy_cost_per_aud)

windows_tested = len(strategy_results)

wins = sum(
    strategy < baseline
    for strategy, baseline
    in zip(strategy_results, baseline_results)
)

losses = sum(
    strategy > baseline
    for strategy, baseline
    in zip(strategy_results, baseline_results)
)

ties = windows_tested - wins - losses

average_baseline_rate = mean(baseline_results)
average_strategy_rate = mean(strategy_results)

improvement_per_aud = (
    average_baseline_rate - average_strategy_rate
)

estimated_saving = (
    improvement_per_aud * TRANSFER_AMOUNT_AUD
)

print("Transfer advice backtest")
print("------------------------")
print("Historical windows tested:", windows_tested)
print(
    "First starting date:",
    dates[HISTORY_DAYS],
)
print(
    "Last starting date:",
    dates[
        len(rates)
        - TRANSFER_WINDOW_DAYS
        - 1
    ],
)
print(
    "Transfer window:",
    TRANSFER_WINDOW_DAYS,
    "days",
)
print(
    "Strategy wins:",
    wins,
    f"({wins / windows_tested * 100:.1f}%)",
)
print(
    "Strategy losses:",
    losses,
    f"({losses / windows_tested * 100:.1f}%)",
)
print("Ties:", ties)
print()
print(
    "Transfer-now average rate:",
    round(average_baseline_rate, 2),
    "VND per AUD",
)
print(
    "Advice strategy average rate:",
    round(average_strategy_rate, 2),
    "VND per AUD",
)
print(
    "Average improvement:",
    round(improvement_per_aud, 2),
    "VND per AUD",
)
print(
    f"Estimated difference for {TRANSFER_AMOUNT_AUD:,.0f} AUD:",
    f"{estimated_saving:,.0f} VND",
)
print()
print(
    "Positive improvement means the advice strategy "
    "beat transferring everything immediately."
)
print(
    "Transfer fees are not included in this backtest."
)