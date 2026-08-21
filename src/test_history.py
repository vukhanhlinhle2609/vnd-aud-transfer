import requests

url = "https://www.vietcombank.com.vn/api/exchangerates"
response = requests.get(url, params={"date": "2026-08-21"}, timeout=10)
data = response.json()

print("Date returned:", data["Date"])

for row in data["Data"]:
    if row["currencyCode"] == "AUD":
        print("JSON sell rate:", row["sell"])
        print("JSON transfer: ", row["transfer"])
        print("JSON cash:     ", row["cash"])