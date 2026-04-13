from dataclasses import dataclass


@dataclass
class BacktestRating:
    """Scores a backtest result on a scale from 0 to 10.

    Scoring weights:
        50% — Final portfolio value (growth above the £1 000 000 initial cash)
        25% — Sharpe ratio        (risk-adjusted returns, threshold = 1.0)
        25% — Maximum drawdown    (risk exposure, threshold = -40%)
    """

    sharpe_threshold: float = 1.0
    max_drawdown_threshold: float = -0.4

    def rate_backtest(self, metrics: dict) -> float:
        """Return a score in [0, 10] from a metrics dict.

        Args:
            metrics: Output of ``TradeSignals.execute_trades()``, with keys
                     ``"Final Portfolio Value"``, ``"Sharpe Ratio"``,
                     ``"Maximum Drawdown"``.

        Returns:
            A float in [0.0, 10.0]. Returns 0.0 if any metric is missing.
        """
        sharpe = metrics.get("Sharpe Ratio")
        drawdown = metrics.get("Maximum Drawdown")
        final_value = metrics.get("Final Portfolio Value")

        if sharpe is None or drawdown is None or final_value is None:
            return 0.0

        # Sharpe score — 25%, capped at 2.5
        sharpe_score = min(2.5, max(0.0, sharpe / self.sharpe_threshold * 2.5))

        # Drawdown score — 25%, capped at 2.5 (smaller drawdown → higher score)
        if drawdown <= self.max_drawdown_threshold:
            drawdown_score = 0.0
        else:
            drawdown_score = min(
                2.5,
                max(0.0, (1 + drawdown / self.max_drawdown_threshold) * 2.5),
            )

        # Portfolio growth score — 50%, capped at 5.0
        growth = final_value / 1_000_000
        growth_score = min(5.0, max(0.0, (growth - 1) * 5))

        return round(min(sharpe_score + drawdown_score + growth_score, 10.0), 2)
