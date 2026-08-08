"""
Financial calculator: CAGR, ROI, and a simplified DCF.

Pure math functions — no data fetching. Takes numbers as input (either
supplied by the user or fetched by another tool first) rather than
trying to forecast cash flows itself.
"""

from __future__ import annotations

from typing import Any


class CalculatorError(Exception):
    """Raised when inputs are invalid for the requested calculation."""


def calculate_cagr(beginning_value: float, ending_value: float, years: float) -> dict[str, Any]:
    if beginning_value <= 0:
        raise CalculatorError("beginning_value must be positive")
    if years <= 0:
        raise CalculatorError("years must be positive")

    cagr = (ending_value / beginning_value) ** (1 / years) - 1
    return {
        "metric": "CAGR",
        "beginning_value": beginning_value,
        "ending_value": ending_value,
        "years": years,
        "result": round(cagr, 6),
        "result_pct": round(cagr * 100, 4),
    }


def calculate_roi(cost: float, gain: float) -> dict[str, Any]:
    if cost <= 0:
        raise CalculatorError("cost must be positive")

    roi = (gain - cost) / cost
    return {
        "metric": "ROI",
        "cost": cost,
        "gain": gain,
        "result": round(roi, 6),
        "result_pct": round(roi * 100, 4),
    }


def calculate_dcf(
    cash_flows: list[float],
    discount_rate: float,
    terminal_value: float = 0.0,
) -> dict[str, Any]:
    """
    Simplified DCF: sums discounted projected cash flows plus a
    discounted terminal value. Cash flows and terminal value are
    supplied inputs, not forecast by this function.
    """
    if not cash_flows:
        raise CalculatorError("cash_flows must contain at least one projected value")
    if discount_rate <= -1:
        raise CalculatorError("discount_rate must be greater than -1")

    present_value = 0.0
    for year, cash_flow in enumerate(cash_flows, start=1):
        present_value += cash_flow / ((1 + discount_rate) ** year)

    if terminal_value:
        present_value += terminal_value / ((1 + discount_rate) ** len(cash_flows))

    return {
        "metric": "DCF",
        "cash_flows": cash_flows,
        "discount_rate": discount_rate,
        "terminal_value": terminal_value,
        "result": round(present_value, 2),
    }


def calculate_financial_metric(metric: str, **kwargs: Any) -> dict[str, Any]:
    """Dispatches to the correct calculator based on the requested metric name."""
    metric_normalized = metric.strip().upper()

    if metric_normalized == "CAGR":
        required = {"beginning_value", "ending_value", "years"}
        missing = required - kwargs.keys()
        if missing:
            raise CalculatorError(f"CAGR requires: {sorted(missing)}")
        return calculate_cagr(kwargs["beginning_value"], kwargs["ending_value"], kwargs["years"])

    if metric_normalized == "ROI":
        required = {"cost", "gain"}
        missing = required - kwargs.keys()
        if missing:
            raise CalculatorError(f"ROI requires: {sorted(missing)}")
        return calculate_roi(kwargs["cost"], kwargs["gain"])

    if metric_normalized == "DCF":
        if "cash_flows" not in kwargs:
            raise CalculatorError("DCF requires: ['cash_flows']")
        return calculate_dcf(
            kwargs["cash_flows"],
            kwargs.get("discount_rate", 0.08),
            kwargs.get("terminal_value", 0.0),
        )

    raise CalculatorError(f"Unknown metric '{metric}'. Supported: CAGR, ROI, DCF")