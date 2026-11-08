import pandas as pd
import os 
datafolder="Prices"

#import data
grid_import=pd.read_csv(os.path.join(datafolder, "Grid_import.csv"))
prices=pd.read_csv(os.path.join(datafolder, "N01prices.csv"))
#Format data
grid_import.rename(columns={"Time":"DateTime"}, inplace=True)
grid_import["DateTime"] = pd.to_datetime(grid_import["DateTime"])
prices["DateTime"] = pd.to_datetime(prices["DateTime"])
#filter to august 
august_grid_import = grid_import[grid_import["DateTime"].dt.month == 8]
august_periods = august_grid_import.merge(
    prices,
	left_on="DateTime",
    right_on="DateTime",
)
#Calculate cost of electricty for each 15 minute period. Divided by 4000 to move from 15minuteW to kWh 
august_periods["Cost"] = (august_periods["W.mean"] * august_periods["Price[NOK/kWh]"])/4000
print(august_periods.head())
print(august_periods["Cost"].sum()) #This should be 716 according to the bill
print(august_periods["W.mean"].sum()/4000) #This should be 500.11 

print(august_periods["DateTime"].unique())
print(august_periods.info)