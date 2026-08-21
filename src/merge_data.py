import csv
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"

with (data_dir / "vcb_aud_history.csv").open() as file:
    history = list(csv.DictReader(file))

with (data_dir / "vcb_aud_rates.csv").open() as file:
    collected = list(csv.DictReader(file))

by_date = {}

for row in history:
    by_date[row["rate_date"]] = row["sell"]

for row in collected:
    day = row["collected_at"][:10]
    by_date[day] = row["sell_rate_vnd"]

out_file = data_dir / "vcb_aud_daily.csv"

with out_file.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["date", "sell"])
    for day in sorted(by_date):
        writer.writerow([day, by_date[day]])

print("Merged", len(by_date), "days into", out_file)