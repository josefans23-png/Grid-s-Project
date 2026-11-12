import os 
import pandas as pd
import datetime as dt
datafolder = "Prices"
"""
Formats the data from Forbrukerrådet into a .csv instead of .xlsx and reformat the time. 
"""
df=pd.read_excel(os.path.join(datafolder,"spotpriser.xlsx")).rename(columns={"Dato/klokkeslett":"DateTime"})

df["DateTime"] =pd.to_datetime(df["DateTime"].str.rsplit("-", n=1).str[0],format="%Y-%m-%d Kl. %H")

df.to_csv(os.path.join(datafolder,"spotpris.csv"),columns=["DateTime","NO1"])
