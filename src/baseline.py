import csv
from pathlib import Path

data_file = Path(__file__).parent.parent / "data" / "vcb_aud_daily.csv"

with data_file.open() as file:
    rows = list(csv.DictReader(file))
rates = [float(row["sell"]) for row in rows]
errors = []
for i in range(1, len(rates)):
    predicted = rates[i - 1]
    actual = rates[i]
    errors.append(abs(actual - predicted))
mae = sum(errors) / len(errors)

print("Days tested:", len(errors))
print("Mean absolute error:", round(mae, 2), "VND")