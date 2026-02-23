from lib.data.Leg import Leg, Strategy, Direction, OptionType
import pandas as pd
from lib.option_strat import query_entries_range_for_strategy, summarize_hold_to_maturity_strategy_from_entries, summarize_strangle_trades, summarize_put_spread_trades
from lib.athena_lib import fetch_strangle_trades, fetch_put_spread_trades
from lib.mysql_lib import create_study, upsert_study_detail, upsert_study_summary
from datetime import datetime
import os

def evaluate_condor(ticker, condor):
    entries = query_entries_range_for_strategy(
            ts_start="2024-07-01",
            ts_end="2026-03-16",
            ticker=ticker,
            strategy=condor,
            mode="nearest",
            require_all_legs=True,
            entry_weekdays={"WED"}
        )
    print("")
    # print(f"wing={wing}, shoulder={shoulder}")
    summary_json, _ = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
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
    summary_json, _ = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
    summary_json["wing"]=wing
    summary_json["shoulder"]=shoulder
    print(summary_json)
    
strangle = Strategy(legs=[
    Leg(direction=Direction.SELL, opt_type=OptionType.CALL, quantity=1, strike_delta=25, dte=30),
    Leg(direction=Direction.SELL, opt_type=OptionType.PUT,  quantity=1, strike_delta=25, dte=30),
])

_STRANGLE_BATCH_SIZE = 100  # scan cost is the same for any # of tickers with bucket partitioning

def strangle_study(tickers, ts_start="2020-12-15", ts_end="2026-03-16", study_description="25-25 strangle"):
    import time

    if isinstance(tickers, str):
        tickers = [tickers]

    common_args = dict(
        ts_start=ts_start,
        ts_end=ts_end,
        call_delta=0.25,
        put_delta=0.25,
        dte=30,
        entry_weekdays={4},  # Friday
    )

    t0 = time.perf_counter()
    all_frames = []
    total_rows = 0
    n_batches = (len(tickers) + _STRANGLE_BATCH_SIZE - 1) // _STRANGLE_BATCH_SIZE
    print(f"Starting strangle study: {len(tickers)} tickers in {n_batches} batches of {_STRANGLE_BATCH_SIZE}")
    for i in range(0, len(tickers), _STRANGLE_BATCH_SIZE):
        batch = tickers[i:i + _STRANGLE_BATCH_SIZE]
        batch_num = i // _STRANGLE_BATCH_SIZE + 1
        t_batch = time.perf_counter()
        print(f"  Batch {batch_num}/{n_batches} ({batch[0]}…{batch[-1]}) ...", end=" ", flush=True)
        df_batch = fetch_strangle_trades(tickers=batch, **common_args)
        elapsed = time.perf_counter() - t_batch
        total_rows += len(df_batch)
        elapsed_total = time.perf_counter() - t0
        eta = (elapsed_total / batch_num) * (n_batches - batch_num)
        print(f"{len(df_batch)} rows  [{elapsed:.1f}s, total {elapsed_total/60:.1f}m, ETA {eta/60:.1f}m]")
        all_frames.append(df_batch)

    df_all = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    t1 = time.perf_counter()
    print(f"\n[TIMING] fetch: {t1-t0:.2f}s  ({total_rows} rows, {len(tickers)} ticker(s))")

    summaries_mid,   detail_mid   = summarize_strangle_trades(df_all, pricing="mid")
    summaries_worst, detail_worst = summarize_strangle_trades(df_all, pricing="worst")

    mid_by_ticker   = {s["ticker"]: s for s in summaries_mid}
    worst_by_ticker = {s["ticker"]: s for s in summaries_worst}

    print("\n=== Comparison ===")
    header = f"{'Ticker':<10} {'N':>6} {'ROC Mid':>10} {'ROC Worst':>10} {'WR Mid':>9} {'WR Worst':>9}"
    print(header)
    print("-" * len(header))
    for ticker in sorted(mid_by_ticker):
        m = mid_by_ticker[ticker]
        w = worst_by_ticker[ticker]
        print(f"{ticker:<10} {m['n_entries']:>6} {m['roc']:>10.1%} {w['roc']:>10.1%} "
              f"{m['win_rate']:>9.1%} {w['win_rate']:>9.1%}")

    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    base_dir = os.path.dirname(os.path.abspath(__file__))

    summary_rows = (
        [{**s, "pricing": "mid"}   for s in summaries_mid] +
        [{**s, "pricing": "worst"} for s in summaries_worst]
    )
    out_df = pd.DataFrame(summary_rows)
    output_path = os.path.join(base_dir, "output", f"strangle_study_{current_time}.csv")
    out_df.to_csv(output_path, index=False)

    detail_mid["pricing"]   = "mid"
    detail_worst["pricing"] = "worst"
    detail_all = pd.concat([detail_mid, detail_worst], ignore_index=True)
    detail_path = os.path.join(base_dir, "output", f"strangle_study_detail_{current_time}.csv")
    detail_all.to_csv(detail_path, index=False)

    study_id         = create_study(study_description)
    detail_affected  = upsert_study_detail(detail_all, study_id)
    summary_affected = upsert_study_summary(summaries_mid, summaries_worst, study_id)

    t2 = time.perf_counter()
    print(f"\n[TIMING] total: {t2-t0:.2f}s")
    print(f"Saved: {output_path}")
    print(f"Saved: {detail_path}")
    print(f"MySQL study_id={study_id}: {detail_affected} rows upserted into study_detail")
    print(f"MySQL study_id={study_id}: {summary_affected} rows upserted into study_summary")

def put_spread_study(tickers, ts_start="2020-12-15", ts_end="2026-03-16",
                     short_delta=0.50, long_delta=0.15,
                     study_description="50-15 put spread"):
    import time

    if isinstance(tickers, str):
        tickers = [tickers]

    common_args = dict(
        ts_start=ts_start,
        ts_end=ts_end,
        short_delta=short_delta,
        long_delta=long_delta,
        dte=30,
        entry_weekdays={4},  # Friday
    )

    t0 = time.perf_counter()
    all_frames = []
    total_rows = 0
    n_batches = (len(tickers) + _STRANGLE_BATCH_SIZE - 1) // _STRANGLE_BATCH_SIZE
    print(f"Starting put spread study: {len(tickers)} tickers in {n_batches} batches of {_STRANGLE_BATCH_SIZE}")
    for i in range(0, len(tickers), _STRANGLE_BATCH_SIZE):
        batch = tickers[i:i + _STRANGLE_BATCH_SIZE]
        batch_num = i // _STRANGLE_BATCH_SIZE + 1
        t_batch = time.perf_counter()
        print(f"  Batch {batch_num}/{n_batches} ({batch[0]}…{batch[-1]}) ...", end=" ", flush=True)
        df_batch = fetch_put_spread_trades(tickers=batch, **common_args)
        elapsed = time.perf_counter() - t_batch
        total_rows += len(df_batch)
        elapsed_total = time.perf_counter() - t0
        eta = (elapsed_total / batch_num) * (n_batches - batch_num)
        print(f"{len(df_batch)} rows  [{elapsed:.1f}s, total {elapsed_total/60:.1f}m, ETA {eta/60:.1f}m]")
        all_frames.append(df_batch)

    df_all = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    t1 = time.perf_counter()
    print(f"\n[TIMING] fetch: {t1-t0:.2f}s  ({total_rows} rows, {len(tickers)} ticker(s))")

    summaries_mid,   detail_mid   = summarize_put_spread_trades(df_all, pricing="mid")
    summaries_worst, detail_worst = summarize_put_spread_trades(df_all, pricing="worst")

    mid_by_ticker   = {s["ticker"]: s for s in summaries_mid}
    worst_by_ticker = {s["ticker"]: s for s in summaries_worst}

    print("\n=== Comparison ===")
    header = f"{'Ticker':<10} {'N':>6} {'ROC Mid':>10} {'ROC Worst':>10} {'WR Mid':>9} {'WR Worst':>9}"
    print(header)
    print("-" * len(header))
    for ticker in sorted(mid_by_ticker):
        m = mid_by_ticker[ticker]
        w = worst_by_ticker[ticker]
        print(f"{ticker:<10} {m['n_entries']:>6} {m['roc']:>10.1%} {w['roc']:>10.1%} "
              f"{m['win_rate']:>9.1%} {w['win_rate']:>9.1%}")

    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    base_dir = os.path.dirname(os.path.abspath(__file__))

    summary_rows = (
        [{**s, "pricing": "mid"}   for s in summaries_mid] +
        [{**s, "pricing": "worst"} for s in summaries_worst]
    )
    out_df = pd.DataFrame(summary_rows)
    output_path = os.path.join(base_dir, "output", f"put_spread_study_{current_time}.csv")
    out_df.to_csv(output_path, index=False)

    detail_mid["pricing"]   = "mid"
    detail_worst["pricing"] = "worst"
    detail_all = pd.concat([detail_mid, detail_worst], ignore_index=True)
    detail_path = os.path.join(base_dir, "output", f"put_spread_study_detail_{current_time}.csv")
    detail_all.to_csv(detail_path, index=False)

    study_id         = create_study(study_description)
    detail_affected  = upsert_study_detail(detail_all, study_id)
    summary_affected = upsert_study_summary(summaries_mid, summaries_worst, study_id)

    t2 = time.perf_counter()
    print(f"\n[TIMING] total: {t2-t0:.2f}s")
    print(f"Saved: {output_path}")
    print(f"Saved: {detail_path}")
    print(f"MySQL study_id={study_id}: {detail_affected} rows upserted into study_detail")
    print(f"MySQL study_id={study_id}: {summary_affected} rows upserted into study_summary")


def condor_study(ticker):
    results = []
    detail_dfs = []
    for i in range(1,3):
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
            summary_json, detail_df = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
            summary_json["wing"]=wing
            summary_json["shoulder"]=shoulder
            results.append(summary_json)
            detail_df["wing"] = wing
            detail_df["shoulder"] = shoulder
            detail_dfs.append(detail_df)
    print(results)

    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    base_dir = os.path.dirname(os.path.abspath(__file__))

    df = pd.DataFrame(results, columns=["shoulder", "wing", "roc", "return_on_credit", "win_rate"])
    output_path = os.path.join(base_dir, "output", f"condor_study_{current_time}.csv")
    df.to_csv(output_path, index=False)

    detail_path = os.path.join(base_dir, "output", f"condor_study_detail_{current_time}.csv")
    pd.concat(detail_dfs, ignore_index=True).to_csv(detail_path, index=False)
