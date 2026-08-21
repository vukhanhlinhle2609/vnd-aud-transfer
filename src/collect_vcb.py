import csv
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
url = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"
response = requests.get(url, timeout=10)
response.raise_for_status()
root = ET.fromstring(response.content)
aud = root.find(".//Exrate[@CurrencyCode='AUD']")
if aud is None:
    raise ValueError("AUD rate was not found")
sell_rate = float(aud.get("Sell").replace(",", ""))
collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
print("Vietcombank AUD selling rate:", sell_rate, "VND")
print("Collected at:", collected_at)
data_file = Path(__file__).parent.parent / "data" / "vcb_aud_rates.csv"
file_exists = data_file.exists()

with data_file.open("a", newline="") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow(["collected_at", "currency", "sell_rate_vnd"])

    writer.writerow([collected_at, "AUD", sell_rate])

print("Saved to:", data_file)