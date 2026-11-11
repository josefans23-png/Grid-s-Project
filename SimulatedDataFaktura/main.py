import pandas as pd















import pandas as pd

INPUT_FILE = "import.txt"

DAY_RATE = 0.3624
LOW_RATE = 0.2124
INTERVAL_HOURS = 1.0

START_DATE = pd.Timestamp("2026-08-01 00:00:00")

# --- Read the file ---

rows = []

with open(INPUT_FILE, "r", encoding="utf-8-sig") as file:
    for line in file:
        if not line.strip():
            continue

        parts = line.split()

        # Convert t1, t2, t3 ... into hour numbers
        hour_number = int(parts[0].removeprefix("t"))

        # Third column contains the power value
        raw_value = parts[2]

        if raw_value == ".":
            power_kw = float("nan")
        else:
            power_kw = float(raw_value.replace(",", "."))

            # Remove tiny floating-point errors
            if abs(power_kw) < 1e-10:
                power_kw = 0.0

        rows.append((hour_number, power_kw))

export = pd.DataFrame(
    rows, columns=["Hour_Number", "Power_kW"]
)

# --- Convert hour numbers to timestamps ---

export["Time"] = (
    START_DATE
    + pd.to_timedelta(export["Hour_Number"] - 1, unit="h")
)

# --- Convert power to energy ---

export["Energy_kWh"] = (
    export["Power_kW"] * INTERVAL_HOURS
)

# --- Identify weekdays between 06:00 and 22:00 ---

weekday_day = (
    (export["Time"].dt.dayofweek < 5)
    & (export["Time"].dt.hour >= 6)
    & (export["Time"].dt.hour < 22)
)

# --- Separate energy totals ---

total_weekday_energy = export.loc[
    weekday_day, "Energy_kWh"
].sum()

total_night_weekend_energy = export.loc[
    ~weekday_day, "Energy_kWh"
].sum()

# --- Calculate values ---

weekday_value = total_weekday_energy * DAY_RATE

night_weekend_value = (
    total_night_weekend_energy * LOW_RATE
)

# --- Grand totals ---

total_energy = (
    total_weekday_energy
    + total_night_weekend_energy
)

total_value = weekday_value + night_weekend_value

# --- Missing measurements ---

missing_hours = export["Power_kW"].isna().sum()

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







import pandas as pd

INPUT_FILE = "import.txt"
START_DATE = pd.Timestamp("2026-08-01 00:00:00")

# --- Read hourly measurements ---

rows = []

with open(INPUT_FILE, "r", encoding="utf-8-sig") as file:
    for line in file:
        if not line.strip():
            continue

        parts = line.split()

        # Convert t1, t2, ... into hour numbers
        hour_number = int(parts[0].removeprefix("t"))

        # Third column contains the power value
        raw_value = parts[2]

        if raw_value == ".":
            power_kw = float("nan")
        else:
            power_kw = float(raw_value.replace(",", "."))

            # Remove tiny floating-point errors
            if abs(power_kw) < 1e-10:
                power_kw = 0.0

        rows.append((hour_number, power_kw))

df = pd.DataFrame(
    rows, columns=["Hour_Number", "Power_kW"]
)

# --- Convert hour numbers into dates ---

df["Time"] = (
    START_DATE
    + pd.to_timedelta(df["Hour_Number"] - 1, unit="h")
)

# --- Extract date ---

df["Date"] = df["Time"].dt.date

# --- Find highest hourly peak for each day ---

valid_data = df.dropna(subset=["Power_kW"])

daily_peak_indices = (
    valid_data.groupby("Date")["Power_kW"].idxmax()
)

daily_peaks = valid_data.loc[daily_peak_indices]

# --- Select 3 highest peaks from different days ---

top_3 = daily_peaks.nlargest(3, "Power_kW")

# --- Calculate average peak ---

if len(top_3) < 3:
    raise ValueError(
        "Not enough days with valid measurements."
    )

average_peak_kw = top_3["Power_kW"].mean()

# --- Determine capacity price ---

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

# --- Print results ---







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