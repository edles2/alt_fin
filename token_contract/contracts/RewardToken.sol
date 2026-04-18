// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title  RewardToken
 * @notice ERC-20 token used to reward profitable backtesting strategies.
 *
 * A fixed supply of 203 tokens is minted to the deployer at construction.
 * No additional minting is possible, ensuring a transparent and finite
 * reward pool.
 *
 * Deployed on Sepolia testnet:
 * 0xA0f0a2D53b3476c50F2Cf24307F8a1Cd3c758254
 */
contract RewardToken is ERC20 {
    constructor(address initialOwner) ERC20("AltFinanceToken", "ALTFIT") {
        _mint(initialOwner, 203 * 10 ** decimals());
    }
}
