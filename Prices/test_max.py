import os
import pandas as pd

datafolder="Prices"

#import data
grid_io=pd.read_csv(os.path.join(datafolder, "AMS_import_export.csv")).rename(columns={"last_changed": "DateTime", "state": "Power"})
grid_io["DateTime"] = pd.to_datetime(grid_io["DateTime"])

#split into export and import
grid_import=grid_io[grid_io["entity_id"]=="sensor.ams_linje6_p"]
grid_export=grid_io[grid_io["entity_id"]=="sensor.ams_linje6_po"]

#find the peak reading in each clock hour.

def month_maxes(df, month, year ,nmax = 3):
    """Return the maximum value for a given month in a DataFrame with time in DataTime column, and value in Power column"""
    # Filter the DataFrame to the specified month
    df = df[df["DateTime"].dt.year == year]
    df = df[df["DateTime"].dt.month == month]
    hourly_import = (
	df.set_index("DateTime")["Power"]
	.resample("h")
	.max()
    )
    daily_peak_times = hourly_import.groupby(hourly_import.index.date).idxmax()
    daily_peaks = hourly_import.loc[daily_peak_times.to_list()]
    top_days = daily_peaks.nlargest(nmax)
    return top_days

top_3_days = month_maxes(grid_import, 8, 2026, nmax=6)
print(top_3_days)




