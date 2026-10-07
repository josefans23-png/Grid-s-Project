import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split  # deler opp dataen i test og verify
from sklearn.metrics import mean_absolute_error, r2_score  # måle modellen



# leser vp filene
varmepumpe_1 = pd.read_csv("dataforheatpumpML/HeatPump_Jan-Jun2025.csv")
varmepumpe_2 = pd.read_csv("dataforheatpumpML/HeatPump_Jul-Dec2025.csv")
# kombinerer
varmepumpe = pd.concat([varmepumpe_1, varmepumpe_2])

# henter temperatur data
temperatur = pd.read_csv("dataforheatpumpML/eksempel_oslo_temperatur_timefortime.csv")


# gjør "unavaible" til NaN i dataen
varmepumpe["forbruk"] = pd.to_numeric(varmepumpe["state"], errors="coerce")

# Gjør dato leslig
varmepumpe["tid"] = pd.to_datetime(varmepumpe["last_changed"], utc=True)
# Fjerner UTC på enden
varmepumpe["tid"] = varmepumpe["tid"].dt.tz_localize(None)


# Runder ned til timen
varmepumpe["tid"] = varmepumpe["tid"].dt.floor("h")
# fjerner rader uten forbruk (ingenting å lære fra, derfor unødvendig)
varmepumpe = varmepumpe.dropna(subset=["forbruk"])
# pga runder ned til timen, tar gjennomsnitt dersom samme tid på målingene
varmepumpe = varmepumpe.groupby("tid")["forbruk"].mean().reset_index()



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
