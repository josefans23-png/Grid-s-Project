import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split  # deler opp dataen i test og trening
from sklearn.metrics import mean_absolute_error, r2_score  # måle modellen
 
 
 
# Reading in data
bil = pd.read_csv("dataforEVML/202510_108xData.csv", skipinitialspace=True)
# removing sapces from column names
bil.columns = bil.columns.str.strip()


# turn car charger column into numeric, invalid values become NaN (missing)
bil["lading"] = pd.to_numeric(bil["car charger"], errors="coerce")


# Turn date-time into datetime, invalid values become NaT (missing)
bil["tid"] = pd.to_datetime(bil["date-time"], format="%Y%m%d-%H%M%S", errors="coerce")
# remove rows with missing date-time
bil = bil.dropna(subset=["tid"])



# remove rows with missing data
bil = bil.dropna(subset=["lading"])
 
#  Aggregate to minute level, taking the mean of all readings in that minute
bil["tid"] = bil["tid"].dt.floor("min")
bil = bil.groupby("tid")["lading"].mean().reset_index()
 
 
 
# Only keeping the rows where the car is not charging and not in standby
lading = bil[bil["lading"] > 1000].copy()

# Seperate into charging sessions, where a new session starts if the time difference is more than 30 minutes
lading["okt"] = (lading["tid"].diff() > pd.Timedelta("30min")).cumsum()
 
# Make a new dataframe with one row per charging session, with the first and last timestamp, and the total energy used
okter = lading.groupby("okt").agg(
    ankomst=("tid", "first"),
    avreise=("tid", "last"),
    watt_sum=("lading", "sum"),
).reset_index()


# Convert time to hours and energy to kWh  
okter["ankomst_time"] = okter["ankomst"].dt.hour + okter["ankomst"].dt.minute / 60 # 17.5 = 17:30
okter["varighet_t"] = (okter["avreise"] - okter["ankomst"]).dt.total_seconds() / 3600 # i timer
okter["energi_kWh"] = okter["watt_sum"] / 60 / 1000 # kWh

# emove very small charging sessions (less than 1 kWh)
okter = okter[okter["energi_kWh"] >= 1]

# Add a new column for departure time, which is arrival time + duration
okter["avreise_time"] = okter["ankomst_time"] + okter["varighet_t"]

# Calculate statistics for the charging sessions
t_arr = okter["ankomst_time"].quantile(0.5)
t_dep = okter["avreise_time"].quantile(0.5)
E_req = okter["energi_kWh"].quantile(0.9)


# Turn the data into weekday and month. 
okter["ukedag"] = okter["ankomst"].dt.dayofweek   # 0=monday, 6=sunday
okter["maaned"] = okter["ankomst"].dt.month       # 1-12

# inputs
X = okter[["ukedag", "maaned"]]
 
 
# Split the data into training and test sets. Training is 80% 
X_trening, X_test, okter_trening, okter_test = train_test_split(
    X, okter, test_size=0.2, shuffle=True
)
 
 
 
The machine learning step. Predicting arrival time, duration and energy used based on weekday and month.

for mal in ["ankomst_time", "varighet_t", "energi_kWh"]:
    modell = GradientBoostingRegressor(n_estimators=100, random_state=None)
    modell.fit(X_trening, okter_trening[mal])
 
    gjetninger = modell.predict(X_test)
    feil = mean_absolute_error(okter_test[mal], gjetninger)
    r2 = r2_score(okter_test[mal], gjetninger)
 
    print(f"{mal}: gjennomsnitt feil = {feil:.2f}, R2-score = {r2:.2f}")
 
 
 
# Check prediction for a wedensday in march. 
ny_predict = pd.DataFrame({
    "ukedag": [2],
    "maaned": [3],
})
# quantiles p10, p50 og p90
for mal in ["ankomst_time", "varighet_t", "energi_kWh"]:
    for q in [0.1, 0.5, 0.9]:
        modell = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=100, random_state=None)
        modell.fit(X, okter[mal])
        print(f"predicted {mal} P{int(q*100)}: {modell.predict(ny_predict)[0]:.1f}")
