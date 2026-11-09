import pandas as pd 

df = pd.read_csv("august_2026_konvertert.csv")

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
