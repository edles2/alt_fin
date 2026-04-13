"""python203 — tokenized reward system for financial backtesting.

Typical usage::

    from datetime import datetime
    from python203 import VolumeBacktest, BacktestRating, TokenTransfer

    metrics = VolumeBacktest(datetime(2023, 1, 1), datetime(2023, 12, 31)).run()
    score   = BacktestRating().rate_backtest(metrics)
    tx_hash = TokenTransfer(private_key, sender).transfer_tokens_from_rating(recipient, score)
"""

from python203.backtest import TradeSignals, VolumeBacktest
from python203.evaluator import BacktestRating
from python203.token_transfer import TokenTransfer

__version__ = "0.1.0"
__all__ = ["VolumeBacktest", "TradeSignals", "BacktestRating", "TokenTransfer"]
