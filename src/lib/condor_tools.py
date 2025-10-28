from data.Leg import Leg, Strategy, Direction, OptionType
import pandas as pd
from option_strat import query_entries_range_for_strategy, summarize_hold_to_maturity_strategy_from_entries



def evaluate_condor(ticker, condor):
    entries = query_entries_range_for_strategy(
            ts_start="2025-07-01",
            ts_end="2026-03-16",
            ticker=ticker,
            strategy=condor,
            mode="nearest",
            require_all_legs=True,
            entry_weekdays={"WED"}
        )
    print("")
    # print(f"wing={wing}, shoulder={shoulder}")
    summary_json = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
    # summary_json["wing"]=wing
    #summary_json["shoulder"]=shoulder
    print(summary_json)

def evaluate_symmetric_condor(ticker, shoulder, wing):
    condor = Strategy(legs=[
            Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=shoulder, dte=30),
            Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=shoulder, dte=30),
            Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=wing, dte=30),
            Leg(direction=Direction.BUY,  opt_type=OptionType.PUT,  quantity=1, strike_delta=wing, dte=30),
         ])
    entries = query_entries_range_for_strategy(
            ts_start="2025-07-01",
            ts_end="2026-03-16",
            ticker=ticker,
            strategy=condor,
            mode="nearest",
            require_all_legs=True,
            entry_weekdays={"WED"}
        )
    print("")
    print(f"wing={wing}, shoulder={shoulder}")
    summary_json = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
    summary_json["wing"]=wing
    summary_json["shoulder"]=shoulder
    print(summary_json)
    
def condor_study(ticker):
    results = []
    for i in range(1,2):
        for j in range(5, 6):
            wing = 5*i
            shoulder = 5*j
            condor = Strategy(legs=[
            Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=shoulder, dte=30),
            Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=shoulder, dte=30),
            Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=wing, dte=30),
            Leg(direction=Direction.BUY,  opt_type=OptionType.PUT,  quantity=1, strike_delta=wing, dte=30),
         ])

        
            entries = query_entries_range_for_strategy(
            ts_start="2020-12-15",
            ts_end="2026-03-16",
            ticker=ticker,
            strategy=condor,
            mode="nearest",
            require_all_legs=True,
            entry_weekdays={"FRI"}
            )
            print("")
            print(f"wing={wing}, shoulder={shoulder}")
            summary_json = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
            summary_json["wing"]=wing
            summary_json["shoulder"]=shoulder
            results.append(summary_json)
    print(results)

    

    df = pd.DataFrame(results, columns=["shoulder", "wing", "roc", "win_rate"])
    df.to_csv("condor.csv", index=False)
