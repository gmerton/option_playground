"""Cumulative intraday volume profile (fraction of a typical RTH session's volume
traded by each 5-minute bin). Copied from ibkr_bot/breakout_monitor.py so the
alert engine has no dependency on the IBKR bot package."""

VOL_PROFILE_CUM = [
    0.0662, 0.0921, 0.1144, 0.1363, 0.1548, 0.1723,
    0.1903, 0.2055, 0.2205, 0.2351, 0.2504, 0.2630,
    0.2779, 0.2903, 0.3021, 0.3159, 0.3285, 0.3416,
    0.3536, 0.3651, 0.3765, 0.3875, 0.3983, 0.4092,
    0.4201, 0.4306, 0.4408, 0.4520, 0.4615, 0.4711,
    0.4821, 0.4910, 0.5001, 0.5085, 0.5175, 0.5245,
    0.5319, 0.5411, 0.5491, 0.5564, 0.5634, 0.5707,
    0.5791, 0.5872, 0.5944, 0.6016, 0.6089, 0.6179,
    0.6274, 0.6352, 0.6439, 0.6524, 0.6605, 0.6676,
    0.6781, 0.6875, 0.6955, 0.7036, 0.7113, 0.7184,
    0.7275, 0.7353, 0.7436, 0.7522, 0.7603, 0.7693,
    0.7790, 0.7879, 0.7984, 0.8097, 0.8213, 0.8334,
    0.8489, 0.8631, 0.8780, 0.8942, 0.9258, 1.0000,
]


def vol_frac(elapsed_min: float) -> float:
    """Fraction of a typical session's volume traded by `elapsed_min` minutes in."""
    if elapsed_min <= 0:
        return VOL_PROFILE_CUM[0]
    binx = int(elapsed_min // 5)
    if binx >= len(VOL_PROFILE_CUM):
        return 1.0
    return VOL_PROFILE_CUM[binx] or VOL_PROFILE_CUM[0]
