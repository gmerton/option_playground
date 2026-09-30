# Sleeping Giants on a point-in-time S&P 500, vs same-date random S&P LEAPs, + cheap-IV gate (2026-09-29)

## Pre-registration
The full pre-registration (universe, detector, arms, vehicle, control, primary bar, IV gate, reported items) is the
docstring of `run_sleeping_giants_sp500.py`, committed with this file BEFORE any run. Do not edit either after results.

Primary in one line: arm B (enter on the breakout above the signal-time resistance) SG LEAP ROC minus the mean of 3
same-date random S&P-member LEAPs, +180 d exit, real fills; t on entry-date clusters ≥ 3, both halves (2020 split)
positive, majority of years positive; top-5 share reported. Secondary: call50_iv percentile ≤ 0.25 at the signal.
