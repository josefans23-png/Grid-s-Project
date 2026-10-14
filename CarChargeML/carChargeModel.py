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



# Removes the data between 2025-07-16 and 2025-10-05
bad_period = (carChargeData["time"] >= "2025-07-16") & (carChargeData["time"] < "2025-10-05")
carChargeData = carChargeData[~bad_period]



# Sorts the data based on time
carChargeData = carChargeData.sort_values("time").reset_index(drop=True)




# Finds out how much time passes between each data, which is 12 hours 0 days
step = carChargeData["time"].diff().median()
step_h = step.total_seconds() / 3600 # Turns the time passed between data from seconds to hours
print(f"Rows: {len(carChargeData)}")
print(f"time step: {step}")
print(f"Max charge_usage: {carChargeData['charge_usage'].max()} W\n")



# Removes the data where the charging is less than 100 W
CHARGING_THRESHOLD_W = 100
charging = carChargeData[carChargeData["charge_usage"] > CHARGING_THRESHOLD_W].copy()




# Energy in each row: W * hours / 1000 = kWh (correct for any time step)
charging["energy_kWh"] = charging["charge_usage"] * step_h / 1000

# A new session starts if the gap to the previous charging row is bigger than 1.5 time steps
charging["session"] = (charging["time"].diff() > step * 1.5).cumsum()

sessions = charging.groupby("session").agg(
    arrival=("time", "first"),
    last_row=("time", "last"),
    energy_kWh=("energy_kWh", "sum"),
).reset_index(drop=True)

# Departure = end of the last time step
sessions["departure"] = sessions["last_row"] + step
sessions["arrival_hour"] = sessions["arrival"].dt.hour + sessions["arrival"].dt.minute / 60
sessions["duration_h"] = (sessions["departure"] - sessions["arrival"]).dt.total_seconds() / 3600
sessions["departure_hour"] = sessions["arrival_hour"] + sessions["duration_h"]   # can be > 24

print("Sessions before size filter:", len(sessions))

# Remove very small sessions (less than 1 kWh)
sessions = sessions[sessions["energy_kWh"] >= 1].reset_index(drop=True)
print("Sessions after size filter:", len(sessions))

if len(sessions) < 20:
    raise SystemExit("Too few charging sessions to train on. Check the time step and threshold above.")
if step_h > 1:
    print("WARNING: time step is over 1 hour, so arrival_hour and duration_h are very rough.")

# ---------- Statistics ----------
t_arr = sessions["arrival_hour"].quantile(0.5)
t_dep = sessions["departure_hour"].quantile(0.5)
E_req = sessions["energy_kWh"].quantile(0.9)
print(f"Median arrival: {t_arr:.1f}, median departure: {t_dep:.1f}, E_req (P90): {E_req:.1f} kWh")

# ---------- Machine learning ----------
sessions["weekday"] = sessions["arrival"].dt.dayofweek   # 0=monday, 6=sunday
sessions["month"] = sessions["arrival"].dt.month         # 1-12

X = sessions[["weekday", "month"]]
targets = ["arrival_hour", "duration_h", "energy_kWh"]

X_train, X_test, s_train, s_test = train_test_split(
    X, sessions, test_size=0.2, shuffle=True, random_state=42
)

for target in targets:
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, s_train[target])
    predictions = model.predict(X_test)
    error = mean_absolute_error(s_test[target], predictions)
    r2 = r2_score(s_test[target], predictions)
    print(f"{target}: mean error = {error:.2f}, R2 = {r2:.2f}")

# ---------- Prediction for a wednesday in march, quantiles P10/P50/P90 ----------
new_predict = pd.DataFrame({"weekday": [2], "month": [3]})

for target in targets:
    for q in [0.1, 0.5, 0.9]:
        model = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=100, random_state=42)
        model.fit(X, sessions[target])
        print(f"predicted {target} P{int(q*100)}: {model.predict(new_predict)[0]:.1f}")
