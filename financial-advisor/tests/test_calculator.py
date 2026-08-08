import pytest

from app.finance.calculator import (
    CalculatorError,
    calculate_cagr,
    calculate_dcf,
    calculate_financial_metric,
    calculate_roi,
)


class TestCalculateCagr:
    def test_correct_cagr(self) -> None:
        result = calculate_cagr(beginning_value=100, ending_value=200, years=5)
        assert result["metric"] == "CAGR"
        assert 0.14 < result["result"] < 0.15  # ~14.87%

    def test_raises_on_nonpositive_beginning_value(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_cagr(beginning_value=0, ending_value=100, years=5)

    def test_raises_on_nonpositive_years(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_cagr(beginning_value=100, ending_value=200, years=0)


class TestCalculateRoi:
    def test_correct_roi(self) -> None:
        result = calculate_roi(cost=100, gain=150)
        assert result["result"] == 0.5

    def test_negative_roi_on_loss(self) -> None:
        result = calculate_roi(cost=100, gain=80)
        assert result["result"] == -0.2

    def test_raises_on_nonpositive_cost(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_roi(cost=0, gain=100)


class TestCalculateDcf:
    def test_basic_dcf(self) -> None:
        result = calculate_dcf(cash_flows=[100, 100, 100], discount_rate=0.10)
        assert result["metric"] == "DCF"
        assert result["result"] > 0
        assert result["result"] < 300  # discounted, so less than undiscounted sum

    def test_dcf_with_terminal_value(self) -> None:
        no_terminal = calculate_dcf(cash_flows=[100, 100], discount_rate=0.10)
        with_terminal = calculate_dcf(cash_flows=[100, 100], discount_rate=0.10, terminal_value=1000)
        assert with_terminal["result"] > no_terminal["result"]

    def test_raises_on_empty_cash_flows(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_dcf(cash_flows=[], discount_rate=0.10)


class TestCalculateFinancialMetric:
    def test_dispatches_to_cagr(self) -> None:
        result = calculate_financial_metric("CAGR", beginning_value=100, ending_value=200, years=5)
        assert result["metric"] == "CAGR"

    def test_dispatches_case_insensitively(self) -> None:
        result = calculate_financial_metric("cagr", beginning_value=100, ending_value=200, years=5)
        assert result["metric"] == "CAGR"

    def test_raises_on_missing_required_params(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_financial_metric("CAGR", beginning_value=100)

    def test_raises_on_unknown_metric(self) -> None:
        with pytest.raises(CalculatorError):
            calculate_financial_metric("UNKNOWN")