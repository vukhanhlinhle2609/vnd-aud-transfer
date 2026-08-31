import csv
from pathlib import Path
from statistics import mean

import streamlit as st


data_file = (
    Path(__file__).parent
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
    st.error("At least 31 days of rate data are required.")
    st.stop()

dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]

latest = rates[-1]
previous = rates[-2]

previous_30_rates = rates[-31:-1]
average_7 = mean(previous_30_rates[-7:])
average_30 = mean(previous_30_rates)

st.title("VND → AUD Transfer Optimiser")

st.metric(
    "Vietcombank AUD selling rate",
    f"{latest:,.2f} VND",
    delta=f"{latest - previous:+,.2f} vs yesterday",
    delta_color="inverse",
)

st.caption("Last updated: " + dates[-1])
st.caption("A lower VND-per-AUD rate is better.")

st.subheader("How good is today?")

historical_rates = rates[:-1]
better_than = sum(
    rate > latest
    for rate in historical_rates
)

percentile = (
    better_than
    / len(historical_rates)
    * 100
)

st.write(
    f"Today's rate is better than "
    f"**{percentile:.0f}%** of earlier recorded days."
)

recent_rates = rates[-91:-1]
better_recent = sum(
    rate > latest
    for rate in recent_rates
)

recent_percentile = (
    better_recent
    / len(recent_rates)
    * 100
)

st.write(
    f"Better than **{recent_percentile:.0f}%** "
    f"of the previous 90 days."
)

st.write(
    f"Previous 7-day average: "
    f"**{average_7:,.2f} VND/AUD**"
)

st.write(
    f"Previous 30-day average: "
    f"**{average_30:,.2f} VND/AUD**"
)

st.subheader("Rate history")

chart_data = {
    "date": dates,
    "VND per AUD": rates,
}

st.line_chart(
    chart_data,
    x="date",
    y="VND per AUD",
)

st.subheader("VND to AUD calculator")

vnd_amount = st.number_input(
    "VND amount",
    min_value=1_000_000,
    value=56_000_000,
    step=1_000_000,
)

st.write(
    f"Estimated amount received: "
    f"**A${vnd_amount / latest:,.2f}**"
)

st.divider()
st.subheader("Transfer budget planner")

aud_amount = st.number_input(
    "AUD amount to transfer",
    min_value=1.0,
    value=3000.0,
    step=100.0,
)

days_remaining = st.number_input(
    "Days until the transfer deadline",
    min_value=0,
    value=14,
    step=1,
)

use_budget = st.checkbox(
    "Set a maximum VND budget"
)

maximum_budget_vnd = None

if use_budget:
    maximum_budget_vnd = st.number_input(
        "Maximum VND budget",
        min_value=1_000_000,
        value=57_000_000,
        step=100_000,
    )

current_cost = aud_amount * latest
average_30_cost = aud_amount * average_30
average_cost_difference = (
    average_30_cost - current_cost
)

st.write(
    f"Current cost for {aud_amount:,.2f} AUD: "
    f"**{current_cost:,.0f} VND**"
)

if average_cost_difference >= 0:
    st.success(
        f"Today costs approximately "
        f"{average_cost_difference:,.0f} VND less "
        f"than the previous 30-day average."
    )
else:
    st.warning(
        f"Today costs approximately "
        f"{abs(average_cost_difference):,.0f} VND more "
        f"than the previous 30-day average."
    )

if maximum_budget_vnd is not None:
    maximum_affordable_rate = (
        maximum_budget_vnd / aud_amount
    )

    budget_difference = (
        maximum_budget_vnd - current_cost
    )

    st.write(
        f"Maximum affordable rate: "
        f"**{maximum_affordable_rate:,.2f} VND/AUD**"
    )

    if budget_difference >= 0:
        st.success(
            f"Within budget by "
            f"{budget_difference:,.0f} VND."
        )
    else:
        st.error(
            f"Over budget by "
            f"{abs(budget_difference):,.0f} VND."
        )

else:
    st.info(
        "No maximum budget has been provided."
    )

if days_remaining <= 2:
    st.warning(
        "Your deadline is close. Historical testing found "
        "no reliable advantage from waiting."
    )

st.info(
    "No validated timing edge has been found. "
    "This dashboard provides historical context and "
    "budget calculations, not a guaranteed forecast."
)

with st.expander("Model evaluation results"):
    st.write(
        "Naive one-day forecast MAE: "
        "**47.59 VND per AUD**."
    )
    st.write(
        "Walk-forward regression MAE: **56.51 VND**, "
        "compared with **53.06 VND** for the baseline. "
        "The regression model was discarded."
    )
    st.write(
        "The tested 14-day timing strategy was "
        "**5.79 VND per AUD worse** than transferring "
        "immediately on average, so it was discarded."
    )