import csv
from pathlib import Path
data_file = Path(__file__).parent.parent / "data" / "vcb_aud_daily.csv"
with data_file.open() as file:
    rows = list(csv.DictReader(file))
dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]
features = []
for i in range(30, len(rates)):
    ma7 = sum(rates[i - 7:i]) / 7
    ma30 = sum(rates[i - 30:i]) / 30
    features.append({
    "date": dates[i],
    "actual_rate": rates[i],
    "ma7": ma7,
    "ma30": ma30,
})
latest = features[-1]

print("Feature date:", latest["date"])
print("Actual rate:", round(latest["actual_rate"], 2))
print("Past 7-day average:", round(latest["ma7"], 2))
print("Past 30-day average:", round(latest["ma30"], 2))