import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score



def to_watt(valueFromCSV):
    number, unit = valueFromCSV.split()
    number = float(number)
    if unit == "kW":
        number *= 1000
    elif unit == "mW":
        number *= 0.001
    return number


# Reads the carChargingUsage-file and makes the date readable for python
def read_carCharge_data(fileName):
    ccd = pd.read_csv(fileName) # Reading the .csv file
    ccd.columns = ["time", "charge_usage"] # Changing the name of the columns from "Time" to "time" and "W.mean { entity_id: u05_billader16a_active_power }" to "charge_usage"
    ccd["time"] = pd.to_datetime(ccd["time"])
    ccd["charge_usage"] = ccd["charge_usage"].apply(to_watt).abs() # apply(to_watt) makes every value to correct format, abs() makes every value positive
    return ccd


# Reading in data
carChargeData = read_carCharge_data("carChargeData_2024_02_23_to_2026_10_13.csv")

# Removes row/data if either charge_usage_data is missing or date/time is missing
carChargeData = carChargeData.dropna()



# Removes the data where the charging wasnt recorded
bad_period = (carChargeData["time"] >= "2025-07-16") & (carChargeData["time"] < "2025-10-05")
carChargeData = carChargeData[~bad_period]



# Makes a new column that calculates Watt to Watt-hour for each data
carChargeData["energy_kWh"] = carChargeData["charge_usage"] * 12 / 1000

# Where the charge_usage is less than 500, we say that the car isnt charging
carChargeData.loc[carChargeData["charge_usage"] < 500, "energy_kWh"] = 0


# Makes a new column where it only includes the date
carChargeData["date"] = carChargeData["time"].dt.date

# Makes a new table where each data is grouped by date, and sums the kWh from them
daily = carChargeData.groupby("date")["energy_kWh"].sum().reset_index()
daily["date"] = pd.to_datetime(daily["date"])

# Adds a new column to the table where it tells which day of the week it is, other, the month
daily["weekday"] = daily["date"].dt.dayofweek
daily["month"] = daily["date"].dt.month


# Adds a new column where it tells if the car has been charging that day
daily["charged"] = daily["energy_kWh"] > 1



# Makes a new table where there is only data of when the car is charging
charging_days = daily[daily["charged"]]
print(f"Percentage of the days charging: {daily["charged"].mean():.0%}")
print(f"Median amount charging: {charging_days['energy_kWh'].median()} kWh")
print(f"90% of all charging: {charging_days['energy_kWh'].quantile(0.9):.1f} kWh")
print("Mean charging for each weekday:")
print(daily.groupby("weekday")["charged"].mean().round(2))



# Inputs for the Model
X = daily[["weekday", "month"]]
# What we want to predict / correct answers
y = daily["energy_kWh"]

# split up the data into test and train 80% and 20%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
model = GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=0.05, random_state=42)
model.fit(X_train, y_train)


predictions = model.predict(X_test)
print(f"\nmean error: {mean_absolute_error(y_test, predictions):.2f} kWh")
print(f"R2-score: {r2_score(y_test, predictions):.2f}")


# use the model to predict how much usage of the day
new_day = pd.DataFrame({"weekday": [2], "month": [3]})
print(f"Predicted energy: {model.predict(new_day)[0]:.1f} kWh")
