# Coinbase API Project

This project interacts with the Coinbase Advanced API to set limit orders for various cryptocurrencies based on a specified investment strategy.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Investment Strategy](#investment-strategy)
- [License](#license)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/coinbase-api-project.git
   ```
2. Navigate to the project directory:
   ```
   cd coinbase-api-project
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python src/dca.py
```

The script will initialize the Coinbase API client, retrieve current prices for BTC, ETH, XRP, ONDO, LINK, AVAX, RNDR, and ARB, and place limit orders based on the defined investment allocations.

## Investment Strategy

The investment allocations are determined based on the existing amount of USDC. The specific allocations for each cryptocurrency are defined within the code. The script runs every four days using GitHub Actions to ensure that the investment strategy is consistently applied.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.