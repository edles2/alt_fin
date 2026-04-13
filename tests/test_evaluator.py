import pytest
from python203.evaluator import BacktestRating


@pytest.fixture
def rater():
    return BacktestRating()


class TestBacktestRating:
    def test_missing_metrics_returns_zero(self, rater):
        assert rater.rate_backtest({}) == 0.0
        assert rater.rate_backtest({"Sharpe Ratio": 1.0}) == 0.0
        assert rater.rate_backtest({"Sharpe Ratio": 1.0, "Maximum Drawdown": -0.1}) == 0.0

    def test_score_is_in_valid_range(self, rater):
        metrics = {
            "Sharpe Ratio": 1.5,
            "Maximum Drawdown": -0.1,
            "Final Portfolio Value": 1_200_000,
        }
        score = rater.rate_backtest(metrics)
        assert 0.0 <= score <= 10.0

    def test_perfect_strategy_scores_ten(self, rater):
        metrics = {
            "Sharpe Ratio": 100.0,
            "Maximum Drawdown": 0.0,
            "Final Portfolio Value": 10_000_000,
        }
        assert rater.rate_backtest(metrics) == 10.0

    def test_losing_strategy_scores_zero(self, rater):
        metrics = {
            "Sharpe Ratio": -2.0,
            "Maximum Drawdown": -0.9,
            "Final Portfolio Value": 500_000,
        }
        assert rater.rate_backtest(metrics) == 0.0

    def test_higher_sharpe_gives_higher_score(self, rater):
        base = {"Maximum Drawdown": -0.2, "Final Portfolio Value": 1_100_000}
        low  = rater.rate_backtest({**base, "Sharpe Ratio": 0.5})
        high = rater.rate_backtest({**base, "Sharpe Ratio": 2.0})
        assert high > low

    def test_smaller_drawdown_gives_higher_score(self, rater):
        base = {"Sharpe Ratio": 1.0, "Final Portfolio Value": 1_100_000}
        bad  = rater.rate_backtest({**base, "Maximum Drawdown": -0.35})
        good = rater.rate_backtest({**base, "Maximum Drawdown": -0.05})
        assert good > bad

    def test_drawdown_below_threshold_scores_zero_component(self, rater):
        metrics = {
            "Sharpe Ratio": 0.0,
            "Maximum Drawdown": rater.max_drawdown_threshold,
            "Final Portfolio Value": 1_000_000,
        }
        assert rater.rate_backtest(metrics) == 0.0
