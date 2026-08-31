import csv
from pathlib import Path
from statistics import mean


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

if len(rows) < 31:
    raise ValueError("At least 31 days of rate data are required.")

latest_row = rows[-1]
latest_date = latest_row["date"]
latest_rate = float(latest_row["sell"])

# Exclude today so all comparisons use past information only.
previous_rates = [
    float(row["sell"])
    for row in rows[-31:-1]
]

average_7 = mean(previous_rates[-7:])
average_30 = mean(previous_rates)

sorted_rates = sorted(previous_rates)
cheap_cutoff = sorted_rates[int((len(sorted_rates) - 1) * 0.25)]
expensive_cutoff = sorted_rates[int((len(sorted_rates) - 1) * 0.75)]

better_than_percent = (
    sum(latest_rate <= rate for rate in previous_rates)
    / len(previous_rates)
    * 100
)

amount_aud = float(
    input("AUD amount to transfer: ").replace(",", "")
)
days_remaining = int(
    input("Days until you must complete the transfer: ")
)

current_cost = amount_aud * latest_rate
average_30_cost = amount_aud * average_30
cost_difference = average_30_cost - current_cost

# The validated naive forecast assumes tomorrow's rate equals today's rate.
baseline_forecast = latest_rate

if days_remaining <= 2:
    recommendation = "TRANSFER NOW"
    reason = "Your deadline is too close to justify waiting."

elif latest_rate <= cheap_cutoff:
    recommendation = "TRANSFER NOW"
    reason = "The current rate is in the cheapest quarter of the past 30 days."

elif latest_rate >= expensive_cutoff and days_remaining >= 8:
    recommendation = "WAIT AND REVIEW DAILY"
    reason = "The current rate is expensive relative to the past 30 days."

else:
    recommendation = "SPLIT THE TRANSFER"
    reason = (
        "Transfer half now and review the remaining half daily "
        "to reduce timing risk."
    )

print()
print("VND to AUD transfer analysis")
print("----------------------------")
print("Latest date:", latest_date)
print("Current rate:", round(latest_rate, 2), "VND per AUD")
print("Past 7-day average:", round(average_7, 2))
print("Past 30-day average:", round(average_30, 2))
print(
    "Current rate is as good as or better than",
    f"{better_than_percent:.1f}% of the previous 30 days.",
)
print(
    "Naive tomorrow forecast:",
    round(baseline_forecast, 2),
    "VND per AUD",
)

print()
print(
    f"Current cost for {amount_aud:,.2f} AUD:",
    f"{current_cost:,.0f} VND",
)

if cost_difference >= 0:
    print(
        "Estimated saving versus the 30-day average:",
        f"{cost_difference:,.0f} VND",
    )
else:
    print(
        "Estimated extra cost versus the 30-day average:",
        f"{abs(cost_difference):,.0f} VND",
    )

print()
print("Recommendation:", recommendation)
print("Reason:", reason)
print()
print("This is a historical decision rule, not a guaranteed forecast.")