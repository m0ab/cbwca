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

def get_max_price_deviation(client, product_id):
    """Get the maximum allowed price deviation for a product."""
    try:
        # Get product details which includes trading rules
        product = client.get_product(product_id)
        # Default to 20% if we can't determine the actual limit
        return 0.20  # Most exchanges limit to 10-20% from current price
    except Exception as e:
        print(f"Failed to get max price deviation for {product_id}: {e}")
        return 0.20  # Conservative default

def place_orders(client, cryptocurrencies, allocations, investment_amount, target_price_adjustment, total_deployed_so_far):
    total_usdc_deployed = 0
    max_usdc_per_run = 1000  # Maximum USDC to deploy per run

    # Check if we would exceed the maximum deployment
    if total_deployed_so_far + (investment_amount * sum(allocations.values())) > max_usdc_per_run:
        print(f"Skipping order set as it would exceed the maximum USDC deployment limit of {max_usdc_per_run}")
        return 0

    for crypto in cryptocurrencies:
        product_id = f"{crypto}-USDC"
        max_deviation = get_max_price_deviation(client, product_id)
        
        # If target adjustment is greater than max allowed, create a ladder of orders
        if target_price_adjustment > max_deviation:
            steps = math.ceil(target_price_adjustment / max_deviation)
            step_size = max_deviation
            step_amount = investment_amount / steps
            
            for step in range(steps):
                current_adjustment = min((step + 1) * step_size, target_price_adjustment)
                
                try:
                    product = client.get_product(product_id)
                    price = float(product["price"])
                    precision = get_precision(crypto)
                    price_precision = get_price_precision(crypto)
                    allocation_amount = step_amount * allocations[crypto]
                    base_size = round(allocation_amount / price, precision)
                    limit_price = round(price * (1 - current_adjustment), price_precision)

                    if base_size > 0:
                        print(f"Placing ladder order {step + 1}/{steps} for {crypto}-USDC at {limit_price} ({current_adjustment*100:.1f}% drop) with base size {base_size}:")
                        print(f"USDC to be used for {crypto}: {allocation_amount}")
                        
                        order_id = f"adj_{current_adjustment:.2f}_{uuid.uuid4()}"
                        order = client.limit_order_gtc_buy(
                            client_order_id=order_id,
                            product_id=product_id,
                            base_size=str(base_size),
                            limit_price=str(limit_price)
                        )
                        
                        if isinstance(order, dict) and order.get('success'):
                            print(f"Order placed: {order}")
                            total_usdc_deployed += allocation_amount
                        else:
                            print(f"Order placement failed: {order}")
                        
                        time.sleep(1)  # Rate limiting delay
                except Exception as e:
                    print(f"Failed to place order for {crypto}-USDC: {e}")
        else:
            # Original single order placement logic for small price adjustments
            try:
                product = client.get_product(product_id)
                price = float(product["price"])
                precision = get_precision(crypto)
                price_precision = get_price_precision(crypto)
                allocation_amount = investment_amount * allocations[crypto]
                base_size = round(allocation_amount / price, precision)
                limit_price = round(price * (1 - target_price_adjustment), price_precision)

                if base_size > 0:
                    print(f"Placing single order for {crypto}-USDC at {limit_price} with base size {base_size}:")
                    print(f"USDC to be used for {crypto}: {allocation_amount}")
                    
                    order_id = f"adj_{target_price_adjustment:.2f}_{uuid.uuid4()}"
                    order = client.limit_order_gtc_buy(
                        client_order_id=order_id,
                        product_id=product_id,
                        base_size=str(base_size),
                        limit_price=str(limit_price)
                    )
                    
                    if isinstance(order, dict) and order.get('success'):
                        print(f"Order placed: {order}")
                        total_usdc_deployed += allocation_amount
                    else:
                        print(f"Order placement failed: {order}")
                    
                    time.sleep(1)  # Rate limiting delay
            except Exception as e:
                print(f"Failed to place order for {crypto}-USDC: {e}")
    
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

    # Updated order configurations with ladder approach for larger drops
    order_configs = [
        {'investment_amount': 300, 'price_adjustment': 0.99},   # 99% drop - creates ladder
        {'investment_amount': 250, 'price_adjustment': 0.95},   # 95% drop - creates ladder
        {'investment_amount': 200, 'price_adjustment': 0.90},   # 90% drop - creates ladder
        {'investment_amount': 100, 'price_adjustment': 0.70},   # 70% drop - creates ladder
        {'investment_amount': 75, 'price_adjustment': 0.50},    # 50% drop - creates ladder
        {'investment_amount': 50, 'price_adjustment': 0.30},    # 30% drop - creates ladder
        {'investment_amount': 15, 'price_adjustment': 0.15},    # 15% drop - single order
        {'investment_amount': 10, 'price_adjustment': 0.05},    # 5% drop - single order
    ]

    total_usdc_deployed = 0
    for config in order_configs:
        deployed = place_orders(client, cryptocurrencies, allocations, config['investment_amount'], 
                              config['price_adjustment'], total_usdc_deployed)
        total_usdc_deployed += deployed
        if total_usdc_deployed >= 1000:  # Stop if we've hit the maximum
            break

    print(f"\nTotal USDC deployed for limit orders: {total_usdc_deployed}")

if __name__ == "__main__":
    main()