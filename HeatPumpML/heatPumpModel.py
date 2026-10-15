import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split  # deler opp dataen i test og verify
from sklearn.metrics import mean_absolute_error, r2_score  # måle modellen



"""
Data is like this:
2024-11-01 07:00:00,500 mW
2024-11-01 13:00:00,1.13 kW
2024-11-01 19:00:00,1.17 W

So we must remove mW, kW and W and change the value to numbers without prefixes. 
500 mW --> 0.5  
1.13 kW --> 1130
1.17 W --> 1.17
"""
def to_watt(valueFromCSV):
    number, unit = valueFromCSV.split()
    number = float(number)
    if unit == "kW":
        number *= 1000
    elif unit == "mW":
        number *= 0.001
    return number


# Reads the heatpump-files and makes the date readable for python
def read_heatpump_data(fileName):
    hpd = pd.read_csv(fileName) # Reading the .csv file
    hpd.columns = ["time", "power_w"] # Changing the name of the columns from "Time" to "time" and "W.mean { entity_id: 11_varmepumpe32a_active_power }" to "power_w"
    hpd["time"] = pd.to_datetime(hpd["time"])
    hpd["power_w"] = hpd["power_w"].apply(to_watt).abs() # apply(to_watt) makes every value to correct format, abs() makes every value positive
    return hpd
heatpumpData_1 = read_heatpump_data("heatpumpData2024_02_18_to_2024_10_30.csv")
heatpumpData_2 = read_heatpump_data("heatpumpData2024_10_31_to_2026_10_13.csv")


# Combines the 2 heatpumpdata's
heatpumpData = pd.concat([heatpumpData_1, heatpumpData_2], ignore_index=True)
# Sorts the data based on time
heatpumpData = heatpumpData.sort_values("time").reset_index(drop=True)



# Reads the temperature data
temperatureData = pd.read_csv(
    "../TemperatureData/temperature_BlindernOslo_2024_02_18_to_2026_10_13.csv", 
    sep=";", 
    decimal=",", 
    usecols=["Tid(norsk normaltid)", "Lufttemperatur"],
)
temperatureData.columns = ["time", "temperature"]
temperatureData["time"] = pd.to_datetime(temperatureData["time"], format="%d.%m.%Y %H:%M")



# Combines temperature data with heatpump data grouped by date and time
data = pd.merge(heatpumpData, temperatureData, on="time")
print("Amount rows:", len(data))


# Removes data between 2025-07-16 and 2025-10-04 because no data recorded
bad_period = (data["time"] >= "2025-07-10") & (data["time"] < "2025-10-05")
data = data[~bad_period].reset_index(drop=True)
print("New amount rows:", len(data))


# Format the data for the Model (Machine learning)
data["hour"] = data["time"].dt.hour # 0-23
data["weekDay"] = data["time"].dt.dayofweek # 0=manday, 6=tuesday
data["month"] = data["time"].dt.month # 1-12



# inputs for the Model
X = data[["temperature", "hour", "weekDay", "month"]]
# what the Model is gonna predict, which is usage of heatpump in Watt
y = data["power_w"]



# Splits the data into learning data and verify data (verify data is used to check how good the model, see r2 score)
X_trening, X_test, y_trening, y_test = train_test_split(
    X, y, test_size=0.2, random_state=78 #78
)



# Machine learning
model = RandomForestRegressor(n_estimators=100, random_state=None)
model.fit(X_trening, y_trening)




# Testing the model
guesses = model.predict(X_test)
mean_errors_power_W = mean_absolute_error(y_test, guesses)

# Getting the r2 score
r2 = r2_score(y_test, guesses)


# Prints out r2 score and average error
print(f"Average error: {mean_errors_power_W:.0f} Watt")
print(f"R2-score: {r2:.2f}")
 
 

# Predict the Watt usage of the heatpump decided date, hour and temperature outside and the Model
new_predict = pd.DataFrame({
    "temperature": [-10],
    "hour": [18],
    "weekDay": [0],
    "month": [1],
})

# Using the model to predict
predicted_usage = model.predict(new_predict)

# Prints out what the Model predicted
print(f"predicted usage: {predicted_usage[0]:.0f} Watt")
