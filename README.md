# python203 — Tokenized Reward System for Financial Backtesting

> Master 203 — Alternative Finance · Paris Dauphine-PSL  
> Amandine Esteve · Edouard Lesbre · Benoit Faivre

## Overview

**python203** bridges quantitative finance and blockchain technology.
Users submit a trading strategy; the package backtests it, scores the result, and automatically rewards the user with ERC-20 tokens proportional to the strategy's performance.

```
Trading strategy ──► Backtest ──► Score (0 – 10) ──► Token transfer
```

---

## Project structure

```
python203/
├── src/python203/
│   ├── backtest.py          # VolumeBacktest  +  TradeSignals
│   ├── evaluator.py         # BacktestRating
│   └── token_transfer.py    # TokenTransfer
├── token_contract/
│   ├── contracts/
│   │   └── RewardToken.sol  # ERC-20 smart contract (Solidity)
│   ├── scripts/
│   │   └── deploy.js        # Hardhat deployment script
│   └── hardhat.config.js
├── scripts/
│   └── track_token.py       # Inspect the token on-chain
├── tests/
│   ├── test_backtest.py
│   └── test_evaluator.py
├── .env.example
└── pyproject.toml
```

---

## Installation

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `INFURA_PROJECT_ID` | Connect to the Sepolia testnet |
| `PRIVATE_KEY` | Sign token transfer transactions |

---

## Usage

### Step 1 — Run a backtest

`VolumeBacktest` fetches historical data for a universe of stocks and applies a volume-based strategy: **buy** when daily volume exceeds 1.5× its 15-day average, **sell** when it falls below 0.5× that average.

```python
from datetime import datetime
from python203 import VolumeBacktest

bt = VolumeBacktest(
    initial_date=datetime(2023, 1, 1),
    final_date=datetime(2023, 12, 31),
)
metrics = bt.run()
# {
#   "Final Portfolio Value": 1_187_432.10,
#   "Sharpe Ratio":          0.83,
#   "Maximum Drawdown":     -0.12,
# }
```

### Step 2 — Score the result

`BacktestRating` maps the three performance metrics to a single score in **[0, 10]**:

| Metric | Weight | Description |
|---|---|---|
| Final Portfolio Value | 50 % | Growth above the initial £1 000 000 |
| Sharpe Ratio | 25 % | Risk-adjusted return (threshold = 1.0) |
| Maximum Drawdown | 25 % | Risk exposure (threshold = −40 %) |

```python
from python203 import BacktestRating

score = BacktestRating().rate_backtest(metrics)
print(f"Score: {score} / 10")
```

### Step 3 — Reward the user with tokens

`TokenTransfer` sends exactly `score` tokens to the recipient's wallet on the Sepolia testnet.

```python
import os
from python203 import TokenTransfer

tt = TokenTransfer(
    private_key=os.environ["PRIVATE_KEY"],
    sender_address="0xYourWalletAddress",
)
tx_hash = tt.transfer_tokens_from_rating(
    recipient="0xRecipientAddress",
    rating=score,
)
print(f"Transaction: {tx_hash}")
```

---

## Token — Master203token (203T)

An ERC-20 token deployed on the **Sepolia testnet** with a **fixed supply of 203 tokens**, minted once to the deployer at deployment. No additional minting is possible, ensuring a transparent and finite reward pool.

| Property | Value |
|---|---|
| Name | Master203token |
| Symbol | 203T |
| Total supply | 203 |
| Contract | `0xA0f0a2D53b3476c50F2Cf24307F8a1Cd3c758254` |
| Network | Ethereum Sepolia testnet |

[View on Sepolia Etherscan →](https://sepolia.etherscan.io/token/0xA0f0a2D53b3476c50F2Cf24307F8a1Cd3c758254)

### Inspect the token

```bash
export INFURA_PROJECT_ID=your_key
python scripts/track_token.py
# optionally pass a wallet address as argument
python scripts/track_token.py 0xYourAddress
```

### Redeploy the contract

```bash
cd token_contract
npm install
npx hardhat run scripts/deploy.js --network sepolia
```

---

## Tests

```bash
pytest
```
