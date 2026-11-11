import pandas as pd

# Read CSV files
usage = pd.read_csv("import.csv")
spot = pd.read_csv("Spot price-data-2026-11-08 23_57_38.csv")

# --- 1. Convert W, kW, MW to kW ---

def to_kw(value):
    if pd.isna(value) or str(value).strip() == "":
        return float("nan")

    parts = str(value).strip().split()
    number = float(parts[0])
    unit = parts[1]

    if unit == "W":
        return number / 1000
    elif unit == "kW":
        return number
    elif unit == "MW":
        return number * 1000
    else:
        raise ValueError(f"Unknown unit: {unit}")

usage["Power_kW"] = usage["W.mean"].apply(to_kw)

# --- 2. Convert timestamps ---

usage["Time"] = pd.to_datetime(usage["Time"])
usage["Hour"] = usage["Time"].dt.floor("h")

spot["Hour"] = pd.to_datetime(
    spot["Time"].str.replace(
        r" Kl\. (\d{2})-\d{2}",
        r" \1:00:00",
        regex=True
    ),
    format="%Y-%m-%d %H:%M:%S"
)

# --- 3. Calculate hourly energy ---

hourly = usage.groupby("Hour").agg(
    Power_sum_kW=("Power_kW", "sum"),
    Measurements=("Power_kW", "count")
).reset_index()

# Only use hours with both half-hour measurements
hourly.loc[
    hourly["Measurements"] != 2,
    "Power_sum_kW"
] = float("nan")

# Each measurement represents 30 minutes = 0.5 hours
hourly["Energy_kWh"] = hourly["Power_sum_kW"] * 0.5

# --- 4. Merge with spot prices ---

result = hourly.merge(
    spot[["Hour", "NOK/kWh.last"]],
    on="Hour",
    how="left",
    validate="one_to_one"
)

# --- 5. Calculate hourly cost ---

result["Cost_NOK"] = (
    result["Energy_kWh"] * result["NOK/kWh.last"]
)

# --- 6. Calculate total ---

total = result["Cost_NOK"].sum()




result.to_csv("hourly_cost.csv", index=False)








import pandas as pd

INPUT_FILE = 'import.csv'
DAY_RATE = 0.3624
LOW_RATE = 0.2124
INTERVAL_HOURS = 0.5

def convert_to_kw(value):
    if pd.isna(value) or not str(value).strip():
        return float('nan')

    parts = str(value).strip().split()

    if len(parts) != 2:
        raise ValueError(f'Unexpected power format: {value!r}')

    number = float(parts[0].replace(',', '.'))
    factors = {'W': 0.001, 'kW': 1, 'MW': 1000}

    if parts[1] not in factors:
        raise ValueError(f'Unknown unit: {parts[1]!r}')

    return number * factors[parts[1]]


# Read data
export = pd.read_csv(INPUT_FILE)
export['Time'] = pd.to_datetime(export['Time'])

# Convert power to energy
export['Power_kW'] = export['W.mean'].apply(convert_to_kw)
export['Energy_kWh'] = export['Power_kW'] * INTERVAL_HOURS

# Identify weekdays between 06:00 and 22:00
weekday_day = (
    (export['Time'].dt.dayofweek < 5) &
    (export['Time'].dt.hour >= 6) &
    (export['Time'].dt.hour < 22)
)

# --- Separate energy totals ---

total_weekday_energy = export.loc[
    weekday_day, 'Energy_kWh'
].sum()

total_night_weekend_energy = export.loc[
    ~weekday_day, 'Energy_kWh'
].sum()

# --- Calculate values ---

weekday_value = total_weekday_energy * DAY_RATE

night_weekend_value = total_night_weekend_energy * LOW_RATE

# --- Grand totals ---

total_energy = (
    total_weekday_energy + total_night_weekend_energy
)

total_value = weekday_value + night_weekend_value

# --- Print results ---









import pandas as pd

# Read export data
export = pd.read_csv("export.csv")

# Convert W, kW, MW to kW
def to_kw(value):
    if pd.isna(value) or str(value).strip() == "":
        return float("nan")

    parts = str(value).strip().split()
    number = float(parts[0])
    unit = parts[1]

    if unit == "W":
        return number / 1000
    elif unit == "kW":
        return number
    elif unit == "MW":
        return number * 1000
    else:
        raise ValueError(f"Unknown unit: {unit}")

# Convert power measurements to kW
export["Power_kW"] = export["W.mean"].apply(to_kw)

# Convert timestamps
export["Time"] = pd.to_datetime(export["Time"])

# Convert 30-minute average power to energy (kWh)
export["Energy_kWh"] = export["Power_kW"] * 0.5

# Sum all available energy measurements
total_kwh = export["Energy_kWh"].sum()






INPUT_FILE = "import.csv"

def convert_to_kw(value):
    if pd.isna(value) or not str(value).strip():
        return float("nan")

    parts = str(value).strip().split()

    if len(parts) != 2:
        raise ValueError(f"Unexpected power format: {value!r}")

    number = float(parts[0].replace(",", "."))
    factors = {"W": 0.001, "kW": 1, "MW": 1000}

    if parts[1] not in factors:
        raise ValueError(f"Unknown unit: {parts[1]}")

    return number * factors[parts[1]]


# Read CSV file
df = pd.read_csv(INPUT_FILE)

# Convert time and power
df["Time"] = pd.to_datetime(df["Time"])
df["Power_kW"] = df["W.mean"].apply(convert_to_kw)

# Group 30-minute readings into hours
df["Hour"] = df["Time"].dt.floor("h")

hourly = df.groupby("Hour").agg(
    Average_kW=("Power_kW", "mean"),
    Measurements=("Power_kW", "count")
).reset_index()

# Only use hours with both 30-minute readings
hourly = hourly[hourly["Measurements"] == 2].copy()

# Extract date
hourly["Date"] = hourly["Hour"].dt.date

# Find highest hourly average for each day
daily_peak_indices = hourly.groupby("Date")["Average_kW"].idxmax()
daily_peaks = hourly.loc[daily_peak_indices]

# Select 3 highest peaks from different days
top_3 = daily_peaks.nlargest(3, "Average_kW")

# Calculate average peak
average_peak_kw = top_3["Average_kW"].mean()


# --- Determine price based on average peak ---

if average_peak_kw < 2:
    price_nok = 150
elif average_peak_kw < 5:
    price_nok = 250
elif average_peak_kw < 10:
    price_nok = 420
elif average_peak_kw < 15:
    price_nok = 585
elif average_peak_kw < 20:
    price_nok = 755
else:
    price_nok = None





overskudd_produksjon = total_kwh*1.0132*-1
print(f"\nOverskudd produksjon: {overskudd_produksjon} NOK")


print("\nSTRØM")
din_strompris = total_energy * 1.7906 + 19
print(f"Din Strømpris: {din_strompris} NOK")


print("\n\nNETTLEIE")
print(f"Weekday value: {weekday_value:.4f} NOK")
print(f"Night/weekend value: {night_weekend_value:.4f} NOK")

Energiledd_pluss_produksjon = -1*total_kwh * 0.05
print(f"Energiledd pluss produksjon: {Energiledd_pluss_produksjon} NOK")

norges_pris = -1*total_energy * 1.29
print(f"NorgesPris: {norges_pris} NOK")

fastledd = price_nok
print(f"Fastledd: {fastledd} NOK")

#Tax
Elavgift = total_energy * 0.0891
print(f"Elavgift: {Elavgift} NOK")

#Tax
energifondet = total_energy * 0.0125
print(f"Energifondet: {energifondet} NOK")


nettleie = weekday_value + night_weekend_value +Energiledd_pluss_produksjon +norges_pris +fastledd +Elavgift + energifondet
print(f"\nNettleie: {nettleie} NOK")




final_price = overskudd_produksjon + din_strompris + nettleie
print(f"\nFinal price: {final_price} NOK")



print(f"\n\n{total_energy}")