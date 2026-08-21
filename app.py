import csv
from pathlib import Path
import streamlit as st

data_file = Path(__file__).parent / "data" / "vcb_aud_daily.csv"

with data_file.open() as file:
    rows = list(csv.DictReader(file))

dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]

latest = rates[-1]
previous = rates[-2]

st.title("VND → AUD Transfer Optimiser")

st.metric(
    "Vietcombank AUD selling rate",
    f"{latest:,.0f} VND",
    delta=f"{latest - previous:+,.0f} vs yesterday",
    delta_color="inverse",
)
st.caption("Last updated: " + dates[-1])

st.subheader("How good is today?")

better_than = sum(1 for r in rates if r > latest)
percentile = better_than / len(rates) * 100

st.write(f"Today's rate is better than **{percentile:.0f}%** of the past year.")

recent = rates[-90:]
better_recent = sum(1 for r in recent if r > latest)
st.write(f"Better than **{better_recent / len(recent) * 100:.0f}%** of the past 90 days.")

st.subheader("Rate history")
st.line_chart({"VND per AUD": rates})

st.subheader("What you'd receive")

amount = st.number_input("VND amount", value=56_000_000, step=1_000_000)
st.write(f"≈ **A${amount / latest:,.2f}**")