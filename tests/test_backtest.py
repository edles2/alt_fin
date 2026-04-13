import pandas as pd
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from python203.backtest import TradeSignals, VolumeBacktest


@pytest.fixture
def price_data():
    """20 days of synthetic OHLCV data for two tickers."""
    tickers = ["AAPL", "MSFT"]
    dates = pd.date_range("2023-01-01", periods=20)
    rows = [
        {
            "ticker": ticker,
            "Date": date,
            "Adj Close": 100.0 + i,
            "Volume": 1_000_000 + (600_000 if i % 3 == 0 else 0),
        }
        for ticker in tickers
        for i, date in enumerate(dates)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def mock_broker():
    broker = MagicMock()
    broker.get_portfolio_value.return_value = 1_000_000.0
    broker.get_cash_balance.return_value = 1_000_000.0
    broker.positions = {}
    return broker


class TestVolumeBacktest:
    def test_compute_signals_adds_position_column(self, price_data):
        vb = VolumeBacktest(datetime(2023, 1, 1), datetime(2023, 1, 31))
        result = vb.compute_signals(price_data)
        assert "Position" in result.columns
        assert result["Position"].isin([-1, 0, 1]).all()

    def test_compute_signals_drops_warmup_rows(self, price_data):
        vb = VolumeBacktest(datetime(2023, 1, 1), datetime(2023, 1, 31))
        result = vb.compute_signals(price_data)
        assert result["Avg Volume"].isna().sum() == 0

    def test_compute_signals_output_is_sorted(self, price_data):
        vb = VolumeBacktest(datetime(2023, 1, 1), datetime(2023, 1, 31))
        result = vb.compute_signals(price_data)
        for ticker, group in result.groupby("ticker"):
            assert list(group["Date"]) == sorted(group["Date"]), (
                f"Dates not sorted for ticker {ticker}"
            )


class TestTradeSignals:
    def test_returns_required_keys(self, mock_broker):
        data = pd.DataFrame([
            {"ticker": "AAPL", "Date": pd.Timestamp("2023-01-01"),
             "Adj Close": 150.0, "Position": 0},
            {"ticker": "AAPL", "Date": pd.Timestamp("2023-01-02"),
             "Adj Close": 152.0, "Position": 0},
        ])
        result = TradeSignals(broker=mock_broker).execute_trades(data)
        assert {"Final Portfolio Value", "Sharpe Ratio", "Maximum Drawdown"} == set(result)

    def test_raises_without_position_column(self, mock_broker):
        data = pd.DataFrame([
            {"ticker": "AAPL", "Date": pd.Timestamp("2023-01-01"), "Adj Close": 150.0}
        ])
        with pytest.raises(KeyError, match="Position"):
            TradeSignals(broker=mock_broker).execute_trades(data)

    def test_maximum_drawdown_is_non_positive(self, mock_broker):
        data = pd.DataFrame([
            {"ticker": "AAPL", "Date": pd.Timestamp(f"2023-01-{i:02d}"),
             "Adj Close": 100.0 + i, "Position": 0}
            for i in range(1, 10)
        ])
        result = TradeSignals(broker=mock_broker).execute_trades(data)
        assert result["Maximum Drawdown"] <= 0.0
