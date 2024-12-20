# Linear programming solver using PuLP
import pandas as pd
from pulp import *
import os

def pulp_solver():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Get the pulp_raw_data from data/query_result for pulp model
    pulp_raw_df = pd.read_pickle(f"{project_root}/data/query_result/pulp_raw_data.pkl")

    # Get the cost_table_data from data/query_result for pulp model
    cost_df = pd.read_pickle(f"{project_root}/data/query_result/cost_table_data.pkl")

    # Initialize Model
    stock_optim_model = LpProblem("Minimize_Transportation_Cost", LpMinimize)

    # Prepare data needed for decision variable, constraint and objective function
    product = pulp_raw_df["Product_ID"].unique().tolist()
    origin = pulp_raw_df["Warehouse_Loc_ID"].unique().tolist()
    origin.append("Supplier")
    destination = pulp_raw_df["Warehouse_Loc_ID"].unique().tolist()

    origin_supply = {
        (p, o): pulp_raw_df[(pulp_raw_df["Product_ID"]==p) & (pulp_raw_df["Warehouse_Loc_ID"]==o)]["Stock_Level"].iloc[0]
        if o != "Supplier" else 10000 for p in product for o in origin
        }

    destination_demand = {
        (p, d): pulp_raw_df[(pulp_raw_df["Product_ID"]==p) & (pulp_raw_df["Warehouse_Loc_ID"]==d)]["Forecasted_Demand"].iloc[0]
        for p in product for d in destination
        }

    cost = {
        (p, o, d): (
            pulp_raw_df[
                (pulp_raw_df["Product_ID"] == p) &
                (pulp_raw_df["Warehouse_Loc_ID"] == d)
            ]["Supply_Cost_Per_Unit"].iloc[0]
            if o == "Supplier"
            else cost_df[
                (cost_df["Warehouse_Origin"] == o) &
                (cost_df["Warehouse_Destination"] == d)
            ]["Cost"].iloc[0]
            if o != d
            else 0
        )
        for p in product
        for o in origin
        for d in destination
    }


    # Initialize the linear programming problem
    stock_optim_model = LpProblem("Minimize_Transportation_Cost", LpMinimize)

    # Decision variables
    transfer_qty = {
        (p, o, d): LpVariable(f"Transfer_{p}_{o}_{d}", lowBound=0)
        for p in product for o in origin for d in destination
    }

    # Objective function
    stock_optim_model += lpSum(cost[p, o, d] * transfer_qty[p, o, d] for p in product for o in origin for d in destination), "Total_Cost"

    # Supply constraints
    for p in product:
        for o in origin:
            stock_optim_model += (
                lpSum(transfer_qty[p, o, d] for d in destination) <= origin_supply[p, o],
                f"Supply_Constraint_{p}_{o}"
            )

    # Demand constraints
    for p in product:
        for d in destination:
            stock_optim_model += (
                lpSum(transfer_qty[p, o, d] for o in origin) >= destination_demand[p, d],
                f"Demand_Constraint_{p}_{d}"
            )

    # Solve the problem
    stock_optim_model.solve()

    optim = []
    for p, o, d in transfer_qty:
        if o!=d and transfer_qty[p, o, d].varValue > 0:
            qty = int(transfer_qty[p, o, d].varValue)
            optim.append([o, d, p, qty])

    optim_df = pd.DataFrame(optim, columns=["From", "To", "Product_ID", "trfQty"])
    optim_df = optim_df.merge(pulp_raw_df, left_on=["Product_ID", "To"],
                            right_on=["Product_ID", "Warehouse_Loc_ID"], how="left")
    optim_df = optim_df[["From", "To", "Product_ID", "Forecasted_Demand", "trfQty"]]
    optim_df.rename(columns={"Forecasted_Demand":"Demand"}, inplace=True)

    return optim_df