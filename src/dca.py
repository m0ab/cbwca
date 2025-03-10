from coinbase.rest import RESTClient
from json import dumps
import math
import os
import uuid
import time

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

def place_orders(client, cryptocurrencies, allocations, investment_amount, price_adjustment, total_deployed_so_far):
    total_usdc_deployed = 0
    max_usdc_per_run = 1000  # Maximum USDC to deploy per run

    # Check if we would exceed the maximum deployment
    if total_deployed_so_far + (investment_amount * sum(allocations.values())) > max_usdc_per_run:
        print(f"Skipping order set as it would exceed the maximum USDC deployment limit of {max_usdc_per_run}")
        return 0

    for crypto in cryptocurrencies:
        product = client.get_product(f"{crypto}-USDC")
        price = float(product["price"])
        precision = get_precision(crypto)
        price_precision = get_price_precision(crypto)
        allocation_amount = investment_amount * allocations[crypto]
        base_size = round(allocation_amount / price, precision)
        limit_price = round(price * (1 - price_adjustment), price_precision)  # Calculate limit price with adjustment

        if base_size > 0:
            print(f"Placing limit order for {crypto}-USDC at {limit_price} with base size {base_size}:")
            print(f"USDC to be used for {crypto}: {allocation_amount}")
            try:
                # Include price adjustment in client_order_id for later reference
                order_id = f"adj_{price_adjustment:.2f}_{uuid.uuid4()}"
                order = client.limit_order_gtc_buy(
                    client_order_id=order_id,
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
            total_usdc_deployed += allocation_amount
            # Introduce a delay to avoid rate limiting
            time.sleep(1)  # 100ms delay
        else:
            print(f"Skipping order for {crypto}-USDC due to base size being zero or less.")
    
    return total_usdc_deployed

def main():
    api_key = os.getenv('COINBASE_API_KEY')
    api_secret = os.getenv('COINBASE_API_SECRET')

    client = RESTClient(api_key=api_key, api_secret=api_secret)

    cryptocurrencies = ['BTC', 'ETH', 'XRP', 'ONDO', 'LINK', 'AVAX', 'RNDR', 'SOL', 'ENS']

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

    # Updated order configurations with more aggressive price adjustments for larger drops
    order_configs = [
        {'investment_amount': 50, 'price_adjustment': 0.05},    # 5% drop - small position
        {'investment_amount': 100, 'price_adjustment': 0.15},   # 15% drop
        {'investment_amount': 150, 'price_adjustment': 0.30},   # 30% drop
        {'investment_amount': 200, 'price_adjustment': 0.50},   # 50% drop
        {'investment_amount': 250, 'price_adjustment': 0.70},   # 70% drop
        {'investment_amount': 300, 'price_adjustment': 0.90},   # 90% drop
        {'investment_amount': 350, 'price_adjustment': 0.95},   # 95% drop
        {'investment_amount': 400, 'price_adjustment': 0.99},   # 99% drop
    ]

    total_usdc_deployed = 0
    for config in order_configs:
        deployed = place_orders(client, cryptocurrencies, allocations, config['investment_amount'], 
                              config['price_adjustment'], total_usdc_deployed)
        total_usdc_deployed += deployed
        if total_usdc_deployed >= 1000:  # Stop if we've hit the maximum
            break

    print(f"Total USDC deployed for limit orders: {total_usdc_deployed}")

if __name__ == "__main__":
    main()