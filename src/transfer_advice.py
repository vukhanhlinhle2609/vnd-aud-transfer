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

# Exclude today so comparisons use past information only.
previous_rates = [
    float(row["sell"])
    for row in rows[-31:-1]
]

average_7 = mean(previous_rates[-7:])
average_30 = mean(previous_rates)

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

budget_input = input(
    "Maximum VND budget (press Enter to skip): "
).strip().replace(",", "")

if budget_input:
    maximum_budget_vnd = float(budget_input)
else:
    maximum_budget_vnd = None

if amount_aud <= 0:
    raise ValueError("The AUD amount must be greater than zero.")

if days_remaining < 0:
    raise ValueError("Days remaining cannot be negative.")

if maximum_budget_vnd is not None and maximum_budget_vnd <= 0:
    raise ValueError("The VND budget must be greater than zero.")

current_cost = amount_aud * latest_rate
average_30_cost = amount_aud * average_30

average_cost_difference = (
    average_30_cost - current_cost
)

# The validated naive forecast assumes tomorrow equals today.
baseline_forecast = latest_rate

if maximum_budget_vnd is None:
    maximum_affordable_rate = None
    budget_difference = None

    if days_remaining <= 2:
        budget_status = "DEADLINE CLOSE"
        status_reason = (
            "No budget target was provided, and there is no "
            "validated evidence that waiting will improve the rate."
        )
    else:
        budget_status = "NO BUDGET TARGET"
        status_reason = (
            "Historical context is shown, but no validated timing "
            "advantage has been found."
        )

else:
    maximum_affordable_rate = (
        maximum_budget_vnd / amount_aud
    )

    budget_difference = (
        maximum_budget_vnd - current_cost
    )

    if current_cost <= maximum_budget_vnd:
        budget_status = "WITHIN BUDGET"
        status_reason = (
            "The current observed rate fits within your VND budget."
        )

    elif days_remaining <= 2:
        budget_status = "ABOVE BUDGET - DEADLINE CLOSE"
        status_reason = (
            "The current cost exceeds your budget and your deadline "
            "is close. There is no validated evidence that waiting "
            "will improve the rate."
        )

    else:
        budget_status = "ABOVE BUDGET"
        status_reason = (
            "The current cost exceeds your budget. You can adjust "
            "the amount, adjust the budget, or continue monitoring. "
            "No validated timing advantage has been found."
        )

print()
print("VND to AUD transfer analysis")
print("----------------------------")
print("Latest date:", latest_date)
print(
    "Current rate:",
    round(latest_rate, 2),
    "VND per AUD",
)
print(
    "Past 7-day average:",
    round(average_7, 2),
)
print(
    "Past 30-day average:",
    round(average_30, 2),
)
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
print("Days remaining:", days_remaining)

if maximum_budget_vnd is None:
    print("Maximum VND budget: Not provided")

else:
    print(
        "Maximum VND budget:",
        f"{maximum_budget_vnd:,.0f} VND",
    )
    print(
        "Maximum affordable rate:",
        f"{maximum_affordable_rate:,.2f} VND per AUD",
    )

    if budget_difference >= 0:
        print(
            "Budget remaining:",
            f"{budget_difference:,.0f} VND",
        )
    else:
        print(
            "Amount over budget:",
            f"{abs(budget_difference):,.0f} VND",
        )

if average_cost_difference >= 0:
    print(
        "Estimated saving versus the 30-day average:",
        f"{average_cost_difference:,.0f} VND",
    )
else:
    print(
        "Estimated extra cost versus the 30-day average:",
        f"{abs(average_cost_difference):,.0f} VND",
    )

print()
print("Budget status:", budget_status)
print("Reason:", status_reason)
print()
print(
    "This tool provides historical context and budget calculations, "
    "not a guaranteed forecast."
)