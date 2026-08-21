import csv
from pathlib import Path

data_file = Path(__file__).parent.parent / "data" / "vcb_aud_rates.csv"

with data_file.open() as file:
    rows = list(csv.DictReader(file))

print("Number of observations:", len(rows))

latest = rows[-1]

print("Latest rate:", latest["sell_rate_vnd"], "VND")
print("Collected at:", latest["collected_at"])

rates = [float(row["sell_rate_vnd"]) for row in rows]

print("Lowest rate:", min(rates), "VND")
print("Highest rate:", max(rates), "VND")

average = sum(rates) / len(rates)

print("Average rate:", round(average, 2), "VND")
print("AUD for 100,000,000 VND:", round(100_000_000 / rates[-1], 2))