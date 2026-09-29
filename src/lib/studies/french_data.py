"""Ken French data library loaders (monthly). Files in data/cache/french/, downloaded from
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (10_Industry_Portfolios, F-F_Research_Data_Factors)."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

DIR = Path(__file__).resolve().parents[3] / "data" / "cache" / "french"


def _block(path: Path, header: str) -> pd.DataFrame:
    lines = path.read_text().splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip().startswith(header)) + 1
    out = [lines[i]]
    for l in lines[i + 1:]:
        if not l.strip() or not l.strip()[:6].isdigit() or len(l.split(",")[0].strip()) != 6:
            break
        out.append(l)
    df = pd.read_csv(io.StringIO("\n".join(out)), index_col=0)
    df.index = pd.PeriodIndex(df.index.astype(str).str.strip(), freq="M")
    df.columns = [c.strip() for c in df.columns]
    return df.replace([-99.99, -999], pd.NA).astype(float) / 100


def industries10(weight: str = "Value") -> pd.DataFrame:
    return _block(DIR / "10_Industry_Portfolios.csv", f"Average {weight} Weighted Returns -- Monthly")


def factors() -> pd.DataFrame:
    """Mkt-RF, SMB, HML, RF monthly (decimal); adds Mkt = Mkt-RF + RF (total return)."""
    lines = (DIR / "F-F_Research_Data_Factors.csv").read_text().splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip().startswith(",Mkt-RF"))
    out = [lines[i]]
    for l in lines[i + 1:]:
        if len(l.split(",")[0].strip()) != 6:
            break
        out.append(l)
    df = pd.read_csv(io.StringIO("\n".join(out)), index_col=0)
    df.index = pd.PeriodIndex(df.index.astype(str).str.strip(), freq="M")
    df.columns = [c.strip() for c in df.columns]
    df = df.astype(float) / 100
    df["Mkt"] = df["Mkt-RF"] + df["RF"]
    return df
