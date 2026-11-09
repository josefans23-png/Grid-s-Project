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

Variable
    TotalImport "Total kWh bought from the power grid for August";

Equations
    Objective "Decides what to minimize"
    EnergyBalance(t) "Bought electricity - Solar electricity = House usage + heatpump - sold electricity from solar"
    FirstHour "Calculates stored heat at first hour"
    HeatBalance(t) "calculates stored heat, for the rest of the hours"
    PowerLimit(t) "Limit the heatpump usage"
    StorageLimit(t) "limits the heat stored"
    FinalStorage "makes sure enough stored heat for monthly usage";

* Minimize electricity imported
Objective..
    TotalImport =e= sum(t, GridDraw(t));

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

* End with at least as much stored energy
FinalStorage..
    StoredHeat('t744') =g= Sstart;

* Makes model named HeatPump
Model HeatPump /all/;

* Solves the optimization
Solve HeatPump using LP minimizing TotalImport;

Display HP.l, StoredHeat.l, GridDraw.l,
        GridExport.l, TotalImport.l;
