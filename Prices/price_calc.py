import pandas as pd
import os 
datafolder="Prices"

#import data
grid_io=pd.read_csv(os.path.join(datafolder, "AMS_import_export.csv")).rename(columns={"last_changed": "DateTime", "state": "W.mean"})
#grid_import=grid_io[grid_io["entity_id"]=="sensor.ams_linje6_p"]

grid_import=pd.read_csv(os.path.join(datafolder, "Grid_import.csv")).rename(columns={"Time":"DateTime"})
prices=pd.read_csv(os.path.join(datafolder, "spotpris.csv"))
#Format data
grid_import["DateTime"] = pd.to_datetime(grid_import["DateTime"]).dt.tz_localize(None)

prices["DateTime"] = pd.to_datetime(prices["DateTime"])
#filter to august
 
august_grid_import = grid_import[grid_import["DateTime"].dt.year==2026]
august_grid_import = august_grid_import[august_grid_import["DateTime"].dt.month==8]

august_periods = august_grid_import.merge(
    prices,
	on="DateTime"
)
august_periods = august_periods.drop(columns=["Unnamed: 0"], errors="ignore")
#Calculate cost of electricty for each hour 

august_periods["Hour_cost"]=august_periods["W.mean"]*august_periods["NO1"]/1000

total_cost = august_periods["Hour_cost"].sum()
print("Cost/consumption from Grafana")
print(total_cost)
print(august_periods["W.mean"].sum()/1000)
