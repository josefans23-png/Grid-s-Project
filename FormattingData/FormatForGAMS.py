
import pandas as pd

# Read the five CSV files
prediction = pd.read_csv("august2026_predictions.csv")
solar = pd.read_csv("Solar production-data-2026-11-08 22_57_52.csv")
draw = pd.read_csv("Grid draw-data-2026-11-08 22_58_20.csv")
export = pd.read_csv("Grid Export-data-2026-11-08 22_58_14.csv")
price = pd.read_csv("Spot price-data-2026-11-08 23_57_38.csv")

# Convert 30-minute power measurements to hourly energy
def hourly_energy(df, name):
    df["Time"] = pd.to_datetime(df["Time"])

    values = df["W.mean"].astype(str).str.strip()

    df["W.mean"] = pd.to_numeric(
    values.str.replace(r"\s*(kW|W)$", "", regex=True),
    errors="coerce"
    )

    # Convert kW to W
    df.loc[values.str.contains(r"kW$", case=False, na=False), "W.mean"] *= 1000

    # Assumption: missing values represent zero power
    df["W.mean"] = df["W.mean"].fillna(0)

    if df["W.mean"].isna().any():
        print(f"\n{name}: {df['W.mean'].isna().sum()} missing values")
        print(df.loc[df["W.mean"].isna(), ["Time", "W.mean"]].head(20))

    df = df.set_index("Time")

    # Each measurement represents 30 minutes
    return (df["W.mean"] * 0.5 / 1000).resample("h").sum()

solar_h = hourly_energy(solar, "Solar")
draw_h = hourly_energy(draw, "Grid draw")
export_h = hourly_energy(export, "Grid export")

# Prepare prediction
prediction["time"] = pd.to_datetime(prediction["time"])
prediction = prediction.set_index("time")

prediction["predicted"] = prediction["predicted_power_W"] / 1000

# Prepare spot price
price["Time"] = pd.to_datetime(
    price["Time"].str.replace(" Kl. ", " ", regex=False)
                 .str.replace(r"-\d{2}$", "", regex=True),
    format="%Y-%m-%d %H"
)
price["price"] = pd.to_numeric(price["NOK/kWh.last"])
price = price.set_index("Time")

# Combine data
data = pd.DataFrame({
    "predicted": prediction["predicted"],
    "solar": solar_h,
    "draw": draw_h,
    "export": export_h,
    "price": price["price"]
})

data["solar"] = data["solar"].clip(lower=0)

data["otherLoad"] = (
    data["draw"] + data["solar"] - data["export"] - data["predicted"]
).clip(lower=0)

# Check the approximation
if data.isna().any().any():
    raise ValueError("Some hourly values are missing.")

assert len(data) == 744, "Det må være 744 timer"

# Create GAMS input file
with open("input.inc", "w") as f:
    for i, row in enumerate(data.itertuples(), start=1):
        f.write(f"predicted('t{i}') = {row.predicted:.6f};\n")
        f.write(f"solar('t{i}') = {row.solar:.6f};\n")
        f.write(f"otherLoad('t{i}') = {row.otherLoad:.6f};\n")
        f.write(f"price('t{i}') = {row.price:.6f};\n")

print("input.inc created!")