import csv
from pathlib import Path
import matplotlib.pyplot as plt

data_file = Path(__file__).parent.parent / "data" / "vcb_aud_history.csv"

with data_file.open() as file:
    rows = list(csv.DictReader(file))

rows.reverse()

dates = [row["rate_date"] for row in rows]
sell_rates = [float(row["sell"]) for row in rows]

plt.figure(figsize=(12, 5))
plt.plot(dates, sell_rates)
plt.title("Vietcombank AUD selling rate (lower is better for you)")
plt.ylabel("VND per AUD")
plt.xticks(rows_step := range(0, len(dates), 30), [dates[i] for i in rows_step], rotation=45)
plt.tight_layout()
plt.show()