import sys
import pandas as pd


def to_watt(valueFromCSV):
    if pd.isna(valueFromCSV): # If there is missing data on the timestamp, then it will not 
        return float("nan")
    number, unit = valueFromCSV.split()
    number = float(number)
    if unit == "kW":
        number *= 1000
    elif unit == "mW":
        number *= 0.001
    return number


def read_carCharge_data(fileName):
    ccd = pd.read_csv(fileName)
    ccd.columns = ["time", "charge_usage"]
    ccd["time"] = pd.to_datetime(ccd["time"])
    ccd["charge_usage"] = ccd["charge_usage"].apply(to_watt).abs()
    return ccd

# Reads the file
carChargeData = read_carCharge_data("Appliances-data-2026-10-26 00_14_33.csv")

# Sorts the data based on time and remove duplicates
carChargeData = carChargeData.sort_values("time").drop_duplicates("time")


# There was missing hours in the data, for example:
# 11:00 3kW
# 14:00 2kW
# This code adds the missing data like this:
# 11:00 3kW
# 12:00 NaN
# 13:00 NaN
# 14:00 2kW
all_hours = pd.date_range(carChargeData["time"].min(), carChargeData["time"].max(), freq="h")
power = carChargeData.set_index("time")["charge_usage"].reindex(all_hours)
# We do this because we will see 11:00 and 14:00 as 1 charge session, even when its 2 hours gap between them

# Set data to NaN on the period when there was no charging recorded
power[(power.index >= "2025-07-16") & (power.index < "2025-10-05")] = float("nan")

print(f"max: {power.max():.0f} W")

CHARGING_THRESHOLD_W = 1000
MAX_GAP_H = 2 # Gap inside 1 hour still counts as same session, over 1 hour makes a different charging session

charging = power[power > CHARGING_THRESHOLD_W] # Keeps only the data where charging is over 1 kW
session_id = (charging.index.to_series().diff() > pd.Timedelta(hours=MAX_GAP_H)).cumsum() # .diff() checks how long ago was last charging, then > checks if the time from last charging was over 2 hours, then if it is, consum() increase the count, which puts the session ID
"""                 charging session ID
18:00         -           0
19:00         1 h         0
20:00         1 h         0
09:00        13 h         1
10:00         1 h         1
"""

rows = []
one_h = pd.Timedelta(hours=1) # Means 1 hour
for id, hours in charging.groupby(session_id):
    first, last = hours.index[0], hours.index[-1] # Finds when charging starts and when charging ends, and saves in variables "start" and "last"
    inside = power[first:last] # makes a new list and adds all charing in kW data for each hour for this specific charging session

    # Skip sessions where we dont know what happened
    if inside.isna().any():
        continue
    if pd.isna(power.get(first - one_h)) or pd.isna(power.get(last + one_h)):
        continue
    """
    we know 17:00 there was no charging, so we know that 18:00 really was start session
    17:00  0 W
    18:00  3600 W    <- start
    19:00  3700 W    <- end
    20:00  0 W

    If 17:00 was NaN, we dont know if 18:00 really was the start of the session, maybe it was 17:00 or earlier
    17:00  NaN
    18:00  3600 W    <- start
    19:00  3700 W
    20:00  0 W
    """

    # Adds session data to the new list
    rows.append({
        "start": first,
        "end": last + one_h, # end of the last charging hour
        "energy_kWh": inside.sum() / 1000, # W * 1 h / 1000
        "max_power_W": inside.quantile(0.95),
    })

# Transform the list to a table and adds column for each data
sessions = pd.DataFrame(rows)
sessions["start_hour"] = sessions["start"].dt.hour
sessions["duration_h"] = (sessions["end"] - sessions["start"]).dt.total_seconds() / 3600
sessions["avg_power_W"] = sessions["energy_kWh"] * 1000 / sessions["duration_h"]
sessions["end_hour"] = sessions["start_hour"] + sessions["duration_h"] 
sessions["weekday"] = sessions["start"].dt.dayofweek
sessions["month"] = sessions["start"].dt.month



# Removes small sessions
sessions = sessions[sessions["energy_kWh"] >= 1].reset_index(drop=True)



print(f"Median start: {sessions['start_hour'].median():.0f}:00, median end: {sessions['end_hour'].median() % 24:.0f}:00")
print(f"Median duration: {sessions['duration_h'].median():.1f} h, median energy: {sessions['energy_kWh'].median():.1f} kWh")
print(f"Energy P90: {sessions['energy_kWh'].quantile(0.9):.1f} kWh, charger max power: {sessions['max_power_W'].quantile(0.95):.0f} W")



known_per_day = power.notna().groupby(power.index.normalize()).sum() # Find out how much data each day has, for example, monday may have 24 hours data known, while tuesday may have 11 hours of data known
days = pd.DataFrame({"date": known_per_day[known_per_day >= 22].index})
days["weekday"] = days["date"].dt.dayofweek
days["charged"] = days["date"].isin(sessions["start"].dt.normalize())
print(f"\nDays with (almost) complete data: {len(days)}")
print("Share of days with a charging session per weekday (0=monday):")
print(days.groupby("weekday")["charged"].mean().round(2))



sessions["date"] = sessions["start"].dt.normalize()



profile = sessions.groupby("weekday").agg(
    sessions=("energy_kWh", "count"),
    start_hour_median=("start_hour", "median"),
    start_hour_p25=("start_hour", lambda x: x.quantile(0.25)),
    start_hour_p75=("start_hour", lambda x: x.quantile(0.75)),
    duration_h_median=("duration_h", "median"),
    energy_kWh_median=("energy_kWh", "median"),
    energy_kWh_p90=("energy_kWh", lambda x: x.quantile(0.9)),
)


profile.insert(0, "share_days_charging", days.groupby("weekday")["charged"].mean())
profile["end_hour_median"] = profile["start_hour_median"] + profile["duration_h_median"]   # can be > 24
profile["max_power_W"] = sessions["max_power_W"].quantile(0.95)
profile.index = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)
print("\nCharging profile per weekday:")
print(profile.round(2).T)



profile.round(2).to_csv("charging_profile.csv")
print("\nSaved to charging_profile.csv")
