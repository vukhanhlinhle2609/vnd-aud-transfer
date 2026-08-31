import csv
from pathlib import Path
data_file = Path(__file__).parent.parent / "data" / "vcb_aud_daily.csv"
with data_file.open() as file:
    rows = list(csv.DictReader(file))
rates = [float(row["sell"]) for row in rows]
up_days = 0
down_days = 0
unchanged_days = 0
for i in range(1, len(rates)):
    if rates[i] > rates[i - 1]:
        up_days += 1
    elif rates[i] < rates[i - 1]:
        down_days += 1
    else:
        unchanged_days += 1
total_days = up_days + down_days + unchanged_days
print("Days compared:", total_days)
print("Rate increased:", up_days, f"({up_days / total_days * 100:.1f}%)")
print("Rate decreased:", down_days, f"({down_days / total_days * 100:.1f}%)")
print("Rate unchanged:", unchanged_days, f"({unchanged_days / total_days * 100:.1f}%)")