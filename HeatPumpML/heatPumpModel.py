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
    hpd.columns = ["time", "power_w"] # Changing the name of the columns from "Time" to "time" and "W.mean { entity_id: 03a_kjokken_3p_230vl_active_power }" to "power_w"
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





"""
temperatur["tid"] = pd.to_datetime(temperatur["Tidspunkt (UTC)"])
# Fjerner unødvendige data
temperatur = temperatur[["tid", "Verdi (C)"]]


#slår sammen dataene
data = pd.merge(varmepumpe, temperatur, on="tid")
print("Antall rader:", len(data))



#gjør dato og time til features
data["time"] = data["tid"].dt.hour # 0-23
data["ukedag"] = data["tid"].dt.dayofweek # 0=mandag, 6=søndag
data["maaned"] = data["tid"].dt.month # 1-12


# inputs
X = data[["Verdi (C)", "time", "ukedag", "maaned"]]
# prediksjon
y = data["forbruk"]


# Deler opp treningsdata og test data 80/20
X_trening, X_test, y_trening, y_test = train_test_split(
    X, y, test_size=0.2, random_state=None
)




modell = RandomForestRegressor(n_estimators=100, random_state=None)
modell.fit(X_trening, y_trening)




#tester på modellen
gjetninger = modell.predict(X_test)
feil = mean_absolute_error(y_test, gjetninger)


r2 = r2_score(y_test, gjetninger)
 
print(f"Gjennomsnitt feil: {feil:.0f} Watt")
print(f"R2-score: {r2:.2f}")
 
 


ny_predict = pd.DataFrame({
    "Verdi (C)": [-10],
    "time": [18],
    "ukedag": [0],
    "maaned": [1],
})
 
predicted_forbruk = modell.predict(ny_predict)
print(f"predicted usage: {predicted_forbruk[0]:.0f} Watt")
"""
