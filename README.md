# Coinbase API Project

This project interacts with the Coinbase Advanced API to set limit orders for various cryptocurrencies based on a specified investment strategy.

## Table of Contents

- [Usage](#usage)
- [Investment Strategy](#investment-strategy)
- [License](#license)

## Usage

To run the application, execute the following command:
```
python src/dca.py
```

The script will initialize the Coinbase API client, retrieve current prices for BTC, ETH, XRP, ONDO, LINK, AVAX, RNDR, SOL, and ENS, and place limit orders based on the defined investment allocations.
 
## Investment Strategy

The investment allocations are determined based on the existing amount of USDC. The specific allocations for each cryptocurrency are defined within the code. The script places multiple sets of limit orders with different price adjustments and investment amounts:

- One set of orders at price minus 5% with an investment amount of $100.
- One set of orders at price minus 10% with an investment amount of $250.
- One set of orders at price minus 15% with an investment amount of $400.
- One set of orders at price minus 20% with an investment amount of $650.

The script runs every four days using GitHub Actions to ensure that the investment strategy is consistently applied.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.