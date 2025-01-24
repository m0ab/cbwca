from coinbase.rest import RESTClient
from json import dumps
import math
import os
import uuid

def get_precision(crypto):
    # Define the precision for each cryptocurrency
    precision = {
        'BTC': 8,
        'ETH': 8,
        'XRP': 2,
        'ONDO': 2,
        'LINK': 2,
        'AVAX': 8,
        'RNDR': 2,
        'SOL': 2,
        'ENS': 2
    }
    return precision.get(crypto, 2)  # Default to 2 if not specified

def get_price_precision(crypto):
    # Define the price precision for each cryptocurrency
    price_precision = {
        'BTC': 2,
        'ETH': 2,
        'XRP': 4,
        'ONDO': 4,
        'LINK': 2,
        'AVAX': 2,
        'RNDR': 2,
        'SOL': 2,
        'ENS': 2
    }
    return price_precision.get(crypto, 2)  # Default to 2 if not specified

def main():
    api_key = os.getenv('COINBASE_API_KEY')
    api_secret = os.getenv('COINBASE_API_SECRET')

    client = RESTClient(api_key=api_key, api_secret=api_secret)

    cryptocurrencies = ['BTC', 'ETH', 'XRP', 'ONDO', 'LINK', 'AVAX', 'RNDR', 'SOL', 'ENS']
    investment_amount = 150  # Investment amount per day

    allocations = {
        'BTC': 0.30,
        'ETH': 0.20,
        'XRP': 0.10,
        'SOL': 0.10,
        'LINK': 0.10,
        'ENS': 0.05,
        'ONDO': 0.05,
        'AVAX': 0.05,
        'RNDR': 0.05,
    }

    for crypto in cryptocurrencies:
        product = client.get_product(f"{crypto}-USDC")
        price = float(product["price"])
        precision = get_precision(crypto)
        price_precision = get_price_precision(crypto)
        allocation_amount = investment_amount * allocations[crypto]
        base_size = round(allocation_amount / price, precision)
        limit_price = round(price * 0.95, price_precision)  # Correctly calculate limit price as current price minus 5%

        if base_size > 0:
            print(f"Placing limit order for {crypto}-USDC:")
            try:
                order = client.limit_order_gtc_buy(
                    client_order_id=str(uuid.uuid4()),
                    product_id=f"{crypto}-USDC",
                    base_size=str(base_size),
                    limit_price=str(limit_price)
                )
                if order['success']:
                    print(f"Order placed: {order}")
                else:
                    print(f"Order placement failed: {order['error_response']}")
            except Exception as e:
                print(f"Failed to place order for {crypto}-USDC: {e}")
        else:
            print(f"Skipping order for {crypto}-USDC due to base size being zero or less.")

if __name__ == "__main__":
    main()