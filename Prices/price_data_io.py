import os 
import pandas as pd
#Read market prices
#File path
datafolder = "Prices"

"""
Used for reading files from Entso-E and Norges Bank to find the 15 minute price in NOK/KWh for 15 minute periods
"""

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
    df = df.sort_values("TIME_PERIOD").set_index("TIME_PERIOD")
    df.index = df.index.normalize()
    df = df[~df.index.duplicated(keep="last")]

    # Include calendar days missing from the exchange-rate data, copying the
    # rate from the most recent existing date.
    full_period = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df = df.reindex(full_period).ffill()

    return df.rename(columns={"OBS_VALUE": "ExchangeRate"}).rename_axis("DateTime").reset_index()

# Monthly price data from : https://transparency.entsoe.eu/fileLibrary/fileBrowserMode?appState=%7B%22path%22%3A%22%2FTP_export%2FEnergyPrices_12.1.D_r3.1%2F%22%7D  
prices06 = read_prices(os.path.join(datafolder,"Prices_2026_06.csv"))  
prices07 = read_prices(os.path.join(datafolder,"Prices_2026_07.csv"))  
prices08 = read_prices(os.path.join(datafolder,"Prices_2026_08.csv"))
prices09 = read_prices(os.path.join(datafolder,"Prices_2026_09.csv"))
prices= pd.concat([prices06, prices07, prices08, prices09], ignore_index=True)
#Exhange rates from https://query.norges-bank.no/no/EXR?frequency=B&startPeriod=2025-01-01&endPeriod=2026-11-08&currency=EUR
exchange_rate = read_exchange_rate(os.path.join(datafolder,"EXR.csv"))

# Convert both tables to a date-only key, then look up the exchange rate for each price row.
prices["Date"] = prices["DateTime"].dt.normalize().dt.tz_localize(None)
exchange_rate["Date"] = pd.to_datetime(exchange_rate["DateTime"]).dt.normalize()

prices = prices.merge(exchange_rate[["Date", "ExchangeRate"]], on="Date", how="left")
prices["Price[NOK/kWh]"] = prices["Price[Currency/MWh]"] * prices["ExchangeRate"]/1000




# Export timestamps without timezone information
#hourly_prices["DateTime"] = hourly_prices["DateTime"].dt.tz_localize(None)
#hourly_prices.to_csv(os.path.join(datafolder,"N01prices_h.csv"),columns=["DateTime","ExchangeRate","Price[NOK/kWh]"], index=False)



