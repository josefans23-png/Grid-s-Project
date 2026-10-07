import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split  # deler opp dataen i test og trening
from sklearn.metrics import mean_absolute_error, r2_score  # måle modellen
 
 
 
# leser inn filen
bil = pd.read_csv("dataforEVML/202510_108xData.csv", skipinitialspace=True)
# fjerner mellomrom i kolonnenavnene
bil.columns = bil.columns.str.strip()


# gjør "unavailable" til NaN i dataen
bil["lading"] = pd.to_numeric(bil["car charger"], errors="coerce")


# gjør dato leselig, ugyldige datoer blir til NaT (manglende)
bil["tid"] = pd.to_datetime(bil["date-time"], format="%Y%m%d-%H%M%S", errors="coerce")
# fjerner rader med ugyldig dato
bil = bil.dropna(subset=["tid"])



# fjerner rader uten måling (ingenting å lære fra)
bil = bil.dropna(subset=["lading"])
 
# runder ned til minuttet, og tar gjennomsnitt hvis flere målinger i samme minutt
bil["tid"] = bil["tid"].dt.floor("min")
bil = bil.groupby("tid")["lading"].mean().reset_index()
 
 
 
# beholder bare minuttene der bilen lader (over 1000 W, standby er 17 W)
lading = bil[bil["lading"] > 1000].copy()

# gir hver ladeøkt et nummer, ny økt hvis det har gått mer enn 30 min
lading["okt"] = (lading["tid"].diff() > pd.Timedelta("30min")).cumsum()
 
# ladeøkt i rader (ankomst, avreise, energi)
okter = lading.groupby("okt").agg(
    ankomst=("tid", "first"),
    avreise=("tid", "last"),
    watt_sum=("lading", "sum"),
).reset_index()




# gjør om til tall  
okter["ankomst_time"] = okter["ankomst"].dt.hour + okter["ankomst"].dt.minute / 60 # 17.5 = 17:30
okter["varighet_t"] = (okter["avreise"] - okter["ankomst"]).dt.total_seconds() / 3600 # i timer
okter["energi_kWh"] = okter["watt_sum"] / 60 / 1000 # kWh

# fjerner veldig små økter
okter = okter[okter["energi_kWh"] >= 1]

# avreise som klokkeslett (kan bli over 24 hvis bilen drar neste dag)
okter["avreise_time"] = okter["ankomst_time"] + okter["varighet_t"]

# typisk ankomst og avreise (P50), og høyt energibehov (P90)
t_arr = okter["ankomst_time"].quantile(0.5)
t_dep = okter["avreise_time"].quantile(0.5)
E_req = okter["energi_kWh"].quantile(0.9)


# gjør dato til features
okter["ukedag"] = okter["ankomst"].dt.dayofweek   # 0=mandag, 6=søndag
okter["maaned"] = okter["ankomst"].dt.month       # 1-12

# inputs
X = okter[["ukedag", "maaned"]]
 
 
# deler opp treningsdata og testdata 80/20
X_trening, X_test, okter_trening, okter_test = train_test_split(
    X, okter, test_size=0.2, shuffle=True
)
 
 
 

for mal in ["ankomst_time", "varighet_t", "energi_kWh"]:
    modell = GradientBoostingRegressor(n_estimators=100, random_state=None)
    modell.fit(X_trening, okter_trening[mal])
 
    gjetninger = modell.predict(X_test)
    feil = mean_absolute_error(okter_test[mal], gjetninger)
    r2 = r2_score(okter_test[mal], gjetninger)
 
    print(f"{mal}: gjennomsnitt feil = {feil:.2f}, R2-score = {r2:.2f}")
 
 
 
# prediksjon for en ny dag: onsdag i mars
ny_predict = pd.DataFrame({
    "ukedag": [2],
    "maaned": [3],
})
# kvantiler p10, p50 og p90
for mal in ["ankomst_time", "varighet_t", "energi_kWh"]:
    for q in [0.1, 0.5, 0.9]:
        modell = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=100, random_state=None)
        modell.fit(X, okter[mal])
        print(f"predicted {mal} P{int(q*100)}: {modell.predict(ny_predict)[0]:.1f}")
