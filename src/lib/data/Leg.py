from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Optional, Dict, Any

class Direction(Enum):
    BUY = auto()
    SELL = auto()

    @property
    def sign(self)->int:
        return 1 if self is Direction.BUY else -1
    
class OptionType(Enum):
    CALL = auto()
    PUT = auto()

@dataclass(frozen=True)
class Leg:
    """
    A strategy leg specified in *trader language*:
      - direction (buy/sell)
      - option type (call/put)
      - quantity (contracts, integer, can be >1)
      - strike expressed in delta (e.g., 30-delta)
      - target DTE (days to expiration)

    The actual strike/expiry selected on a given entry date is resolved later
    using market data (chain snapshots + expiries calendar).
    """
    direction: Direction
    opt_type: OptionType
    quantity: int
    strike_delta: float  # e.g., 30.0 for 30-delta (always positive)
    dte: int             # target days to expiration (>=1)

    # Optional resolved fields (filled in by a resolver step once chain data is available)
    resolved_expiry: Optional[str] = field(default=None, compare=False)
    resolved_strike: Optional[float] = field(default=None, compare=False)
    entry_price: Optional[float] = field(default=None, compare=False)  # per-contract premium at entry
    exit_price: Optional[float] = field(default=None, compare=False)   # per-contract premium at exit (if early exit)
    
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if not (0 < self.strike_delta <= 100):
            raise ValueError("strike_delta should be in (0, 100], e.g., 30 for 30-delta")
        if self.dte < 1:
            raise ValueError("dte must be >= 1")
    
     # -------- Convenience ----------
    @property
    def is_long(self) -> bool:
        return self.direction is Direction.BUY

    @property
    def is_short(self) -> bool:
        return self.direction is Direction.SELL

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["direction"] = self.direction.name
        d["opt_type"] = self.opt_type.name
        return d

    # -------- Core math (payoff & PnL) ----------
    def payoff_at_expiry(self, underlying_at_expiry: float) -> float:
        """
        Per-contract payoff at expiry (intrinsic value), not including premium sign.
        """
        if self.opt_type is OptionType.CALL:
            return max(0.0, underlying_at_expiry - float(self.resolved_strike or 0.0))
        else:
            return max(0.0, float(self.resolved_strike or 0.0) - underlying_at_expiry)

    def pnl_hold_to_maturity(self, underlying_at_expiry: float) -> float:
        """
        PnL per contract for a hold-to-expiry trade:
          Long:  payoff - entry_price
          Short: entry_price - payoff
        Multiplies by contract multiplier (default 100) elsewhere.
        """
        if self.entry_price is None:
            raise ValueError("entry_price must be set to compute PnL.")

        payoff = self.payoff_at_expiry(underlying_at_expiry)
        # For long, premium is paid upfront; for short, received upfront
        signed = payoff - self.entry_price if self.is_long else self.entry_price - payoff
        return signed

    # -------- Resolution hooks ----------
    def with_resolution(self, *, strike: float, expiry: str, entry_price: float) -> "Leg":
        """
        Return a copy with concrete strike/expiry/entry filled in (immutably).
        """
        return Leg(
            direction=self.direction,
            opt_type=self.opt_type,
            quantity=self.quantity,
            strike_delta=self.strike_delta,
            dte=self.dte,
            resolved_expiry=expiry,
            resolved_strike=strike,
            entry_price=entry_price,
            exit_price=self.exit_price,
        )
    
    # ---------- Example Strategy container (extensible) ----------
@dataclass
class Strategy:
    """
    A strategy is a list of Legs. Execution logic (enter/exit rules) lives outside,
    but this gives us a typed bundle we can pass through the backtest engine.
    """
    legs: list[Leg]

    def to_dict(self) -> Dict[str, Any]:
        return {"legs": [leg.to_dict() for leg in self.legs]}

    @classmethod
    def single_leg(cls,
                   direction: Direction,
                   opt_type: OptionType,
                   quantity: int,
                   strike_delta: float,
                   dte: int) -> "Strategy":
        return cls(legs=[Leg(direction, opt_type, quantity, strike_delta, dte)])
