import pandas as pd 

df = pd.read_csv("exportcsv.txt")

df["Time"] = pd.to_datetime(df["Time"])

liste = df["Value"].tolist()

daily_highest = df.groupby(df["Time"].dt.date)["Value"].max()

daily_highest = list(daily_highest.items())


print("\n\n")

top3 = []

for i in range(3):
    highest = max(daily_highest, key=lambda x: x[1])
    daily_highest.remove(highest)
    top3.append(highest)

print(top3)

#2026-08-31 04:00:00,5.4434
#2026-08-03 05:00:00,4.7715
#2026-08-07 04:00:00,4.5419
# Fastledd "peak usage 5.4 kW" = 420 kr
# 