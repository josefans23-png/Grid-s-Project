import os 
import pandas as pd
#Read market prices
#File path
datafolder = "Prices"
filename = "Prices_2026_06.csv"
file_path = os.path.join(datafolder, filename)

#Read csv file, select columns and filter to NO1
def read_prices(path):
    df = pd.read_csv(path, header=0,sep="\t",usecols=["DateTime(UTC)","AreaMapCode","Price[Currency/MWh]"])
    #Filter to price zone NO1
    noprices = df[df["AreaMapCode"]=="NO1"].reset_index(drop=True)
    #convert time zone to Europe/Oslo
    noprices["DateTime(UTC)"] = pd.to_datetime(noprices["DateTime(UTC)"], utc=True).dt.tz_convert("Europe/Oslo")
    noprices = noprices.rename(columns={"DateTime(UTC)": "DateTime"})
    return noprices

#Reads the csv with exchange rates, and converts it into proper formats. 
def read_exchange_rate(path):
    df=pd.read_csv(path, header=0, sep=";", usecols=["OBS_VALUE", "TIME_PERIOD"],decimal=",")
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    return df.rename(columns={"OBS_VALUE": "ExchangeRate", "TIME_PERIOD": "DateTime"})
    
print(read_prices(file_path).info())
print(read_exchange_rate(os.path.join(datafolder,"EXR.csv")).info())

