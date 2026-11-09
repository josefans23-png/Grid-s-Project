Sets
t /t1*t744/;
* Makes a list of: t1, t2, t3, t4, ...

* Data we have from "input.inc"
Parameters
predicted(t) "Predicted HP Watt consumption (kWh)"
    solar(t) "Solar production (kWh)"
    otherLoad(t) "Other household consumption (kWh)"
    price(t) "Spot price (kr/kWh)";

$include "input.inc"

* Constant variables:
* Pmax = Heatpump maximum usage 3,84 kWh every hour
Scalar Pmax /3.84/;
* Maximum 10 kWh heat can be stored in "VarmeForberederen"
Scalar MaxStorage /10/;
* Assume we have 5 kWh stored heat in "VarmeForbedreden" at the start
Scalar Sstart /5/;

* Always positive variables
Positive Variables
HP(t) "How much electricity Heatpump will use each hour (kWh)"
    GridDraw(t) "Electricity imported (kWh)"
    GridExport(t) "Electricity exported (kWh)"
    StoredHeat(t) "Stored energy (kWh)";

* Means value either 1 or 0 where 0 means can sell electricty and 1 meant cant
Binary Variable BuyMode(t);

Variable TotalCost;

Equations
Objective "Decides what to minimize"
    EnergyBalance(t) "Bought electricity - Solar electricity = House usage + heatpump - sold electricity from solar"
    FirstHour "Calculates stored heat at first hour"
    HeatBalance(t) "calculates stored heat, for the rest of the hours"
    PowerLimit(t) "Limit the heatpump usage"
    StorageLimit(t) "limits the heat stored"
    FinalStorage "makes sure enough stored heat for monthly usage"
    BuyLimit(t)
    SellLimit(t)
    ExportLimit(t);

* Minimize electricity imported
Objective..
    TotalCost =e= sum(t, GridDraw(t)*0.50 - GridExport(t)*price(t));

* Electricity balance
EnergyBalance(t)..
    GridDraw(t) - GridExport(t) =e= otherLoad(t) + HP(t) - solar(t);

* First hour
FirstHour..
    StoredHeat('t1') =e= Sstart + HP('t1') - predicted('t1');

* Remaining hours
HeatBalance(t)$(ord(t)>1)..
    StoredHeat(t) =e= StoredHeat(t-1) + HP(t) - predicted(t);

* Maximum HP consumption per hour
PowerLimit(t)..
    HP(t) =l= Pmax;

* Maximum stored energy
StorageLimit(t)..
    StoredHeat(t) =l= MaxStorage;

*
ExportLimit(t)..
    GridExport(t) =l= max(0, solar(t));

*
BuyLimit(t)..
    GridDraw(t) =l= 100 * BuyMode(t);

*
SellLimit(t)..
    GridExport(t) =l= solar(t) * (1 - BuyMode(t));

* End with at least as much stored energy
FinalStorage..
    StoredHeat('t744') =g= Sstart;

* Makes model named HeatPump
Model HeatPump /all/;

* Solves the optimization
Solve HeatPump using MIP minimizing TotalCost;

Scalar TotalHP, TotalBought, TotalSold;

TotalHP = sum(t, HP.l(t));
TotalBought = sum(t, GridDraw.l(t));
TotalSold = sum(t, GridExport.l(t));

put_utility 'log' / 'TotalHP = ' TotalHP:12:2;
put_utility 'log' / 'TotalBought = ' TotalBought:12:2;
put_utility 'log' / 'TotalSold = ' TotalSold:12:2;

put_utility 'log' / 'TotalCost = ' TotalCost.l:12:2;

Display TotalCost.l;

display price;

Scalar AveragePrice;
AveragePrice = sum(t, price(t)) / card(t);
display AveragePrice;


Scalar AveragePrice, MinPrice, MaxPrice;

AveragePrice = sum(t, price(t)) / card(t);
MinPrice = smin(t, price(t));
MaxPrice = smax(t, price(t));

put_utility 'log' / 'AveragePrice = ' AveragePrice:12:2;
put_utility 'log' / 'MinPrice = ' MinPrice:12:2;
put_utility 'log' / 'MaxPrice = ' MaxPrice:12:2;