import csv
import time
import requests
from pathlib import Path
from datetime import date, timedelta

url = "https://www.vietcombank.com.vn/api/exchangerates"
out_file = Path(__file__).parent.parent / "data" / "vcb_aud_history.csv"

today = date.today()
results = []

for days_ago in range(365):
    target = today - timedelta(days=days_ago)
    day_text = target.isoformat()

    try:
        response = requests.get(url, params={"date": day_text}, timeout=10)
        data = response.json()

        for row in data["Data"]:
            if row["currencyCode"] == "AUD":
                results.append([day_text, row["cash"], row["transfer"], row["sell"]])
                print(day_text, row["sell"])

    except Exception as error:
        print(day_text, "FAILED:", error)

    time.sleep(0.5)

with out_file.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["rate_date", "buy_cash", "buy_transfer", "sell"])
    writer.writerows(results)

print("Saved", len(results), "rows to", out_file)