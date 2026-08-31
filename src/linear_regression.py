import csv
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

data_file = Path(__file__).parent.parent / "data" / "vcb_aud_daily.csv"

with data_file.open() as file:
    rows = list(csv.DictReader(file))
dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]
features = []
targets = []
baseline_predictions = []
feature_dates = []

for i in range(30, len(rates)):
    yesterday = rates[i - 1]
    ma7 = sum(rates[i - 7:i]) / 7
    ma30 = sum(rates[i - 30:i]) / 30
    features.append([yesterday, ma7, ma30])
    targets.append(rates[i])
    baseline_predictions.append(yesterday)
    feature_dates.append(dates[i])
split_index = int(len(features) * 0.8)
X_train = features[:split_index]
X_test = features[split_index:]
y_train = targets[:split_index]
y_test = targets[split_index:]
baseline_test = baseline_predictions[split_index:]
test_dates = feature_dates[split_index:]
model = LinearRegression()
model.fit(X_train, y_train)
model_predictions = model.predict(X_test)
model_mae = mean_absolute_error(y_test, model_predictions)
baseline_mae = mean_absolute_error(y_test, baseline_test)
print("Test period:", test_dates[0], "to", test_dates[-1])
print("Test days:", len(y_test))
print("Baseline MAE:", round(baseline_mae, 2), "VND")
print("Regression MAE:", round(model_mae, 2), "VND")
print("Improvement:", round(baseline_mae - model_mae, 2), "VND")
minimum_training_size = 100
walk_model_predictions = []
walk_baseline_predictions = []
walk_actual = []
for test_index in range(minimum_training_size, len(features)):
    walk_model = LinearRegression()
    walk_model.fit(features[:test_index], targets[:test_index])
    prediction = walk_model.predict([features[test_index]])[0]
    walk_model_predictions.append(prediction)
    walk_baseline_predictions.append(baseline_predictions[test_index])
    walk_actual.append(targets[test_index])
walk_model_mae = mean_absolute_error(walk_actual, walk_model_predictions)
walk_baseline_mae = mean_absolute_error(walk_actual, walk_baseline_predictions)
print("\nWalk-forward validation")
print("Test days:", len(walk_actual))
print("Baseline MAE:", round(walk_baseline_mae, 2), "VND")
print("Regression MAE:", round(walk_model_mae, 2), "VND")
print("Improvement:", round(walk_baseline_mae - walk_model_mae, 2), "VND")