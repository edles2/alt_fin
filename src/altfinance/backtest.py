import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import pandas as pd
from pybacktestchain.broker import Broker
from pybacktestchain.data_module import get_stocks_data

logger = logging.getLogger(__name__)

_RISK_FREE_RATE = 0.01          # annualised
_ROLLING_WINDOW = 15            # days used to compute the average volume
_DEFAULT_UNIVERSE: List[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "TSLA", "NVDA", "INTC", "CSCO", "NFLX",
]


@dataclass
class TradeSignals:
    """Executes trades from a pre-computed signal column and returns metrics.

    Expects a DataFrame with columns: Date, ticker, Adj Close, Position.
    Position values: +1 (buy), -1 (sell), 0 (hold).
    """

    broker: Broker
    max_allocation: float = 0.15   # max fraction of available cash per position

    def execute_trades(self, data: pd.DataFrame) -> dict:
        """Run all trades and compute performance metrics.

        Returns:
            dict with keys ``"Final Portfolio Value"``, ``"Sharpe Ratio"``,
            ``"Maximum Drawdown"``.

        Raises:
            KeyError: if ``data`` has no ``"Position"`` column.
        """
        if "Position" not in data.columns:
            raise KeyError("'Position' column is missing — call compute_signals() first.")

        portfolio_values = []

        for date in sorted(data["Date"].unique()):
            day = data[data["Date"] == date]
            prices = dict(zip(day["ticker"], day["Adj Close"]))
            portfolio_values.append({
                "Date": date,
                "Portfolio Value": self.broker.get_portfolio_value(market_prices=prices),
            })

            for _, row in day.iterrows():
                ticker, signal, price = row["ticker"], row["Position"], row["Adj Close"]
                max_qty = int(self.broker.get_cash_balance() * self.max_allocation / price)

                if signal == 1 and max_qty > 0:
                    self.broker.buy(ticker, max_qty, price, date)
                elif signal == -1 and ticker in self.broker.positions:
                    self.broker.sell(ticker, self.broker.positions[ticker].quantity, price, date)

        df = pd.DataFrame(portfolio_values)
        final_value = df.iloc[-1]["Portfolio Value"]

        daily_returns = df["Portfolio Value"].pct_change().dropna()
        excess_returns = daily_returns - (_RISK_FREE_RATE / 252)
        sharpe = (
            excess_returns.mean() / excess_returns.std()
            if excess_returns.std() != 0
            else 0.0
        )

        rolling_max = df["Portfolio Value"].cummax()
        max_drawdown = ((df["Portfolio Value"] - rolling_max) / rolling_max).min()

        logger.info("Final portfolio value: %s", final_value)
        logger.info("Sharpe ratio:          %.4f", sharpe)
        logger.info("Maximum drawdown:      %.4f", max_drawdown)

        return {
            "Final Portfolio Value": final_value,
            "Sharpe Ratio": sharpe,
            "Maximum Drawdown": max_drawdown,
        }


@dataclass
class VolumeBacktest:
    """Volume-based trading strategy.

    Generates a **buy** signal when daily volume exceeds 1.5× its
    ``_ROLLING_WINDOW``-day average, and a **sell** signal when it falls
    below 0.5× that average.

    Example::

        from datetime import datetime
        from altfinance import VolumeBacktest

        bt = VolumeBacktest(
            initial_date=datetime(2023, 1, 1),
            final_date=datetime(2023, 12, 31),
        )
        metrics = bt.run()
    """

    initial_date: datetime
    final_date: datetime
    universe: List[str] = field(default_factory=lambda: list(_DEFAULT_UNIVERSE))
    initial_cash: int = 1_000_000
    verbose: bool = True
    broker: Broker = field(init=False)

    def __post_init__(self):
        self.broker = Broker(cash=self.initial_cash, verbose=self.verbose)

    def compute_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add a ``Position`` column to *data* (+1, -1 or 0)."""
        data = data.sort_values(["ticker", "Date"])
        data["Avg Volume"] = data.groupby("ticker")["Volume"].transform(
            lambda x: x.rolling(_ROLLING_WINDOW).mean()
        )
        data["Position"] = 0
        data.loc[data["Volume"] > data["Avg Volume"] * 1.5, "Position"] = 1
        data.loc[data["Volume"] < data["Avg Volume"] * 0.5, "Position"] = -1
        # Drop the first (_ROLLING_WINDOW - 1) rows per ticker where Avg Volume
        # is not yet defined.
        return data.dropna(subset=["Avg Volume"])

    def run(self) -> dict:
        """Fetch data, compute signals, execute trades and return metrics."""
        logger.info(
            "Running VolumeBacktest on %d tickers from %s to %s",
            len(self.universe),
            self.initial_date.date(),
            self.final_date.date(),
        )
        data = get_stocks_data(self.universe, self.initial_date, self.final_date)
        data = self.compute_signals(data)
        return TradeSignals(broker=self.broker).execute_trades(data)
