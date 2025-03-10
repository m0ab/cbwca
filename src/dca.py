from coinbase.rest import RESTClient
from json import dumps
import math
import os
import uuid
import time
from datetime import datetime

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
        # Conservative limit of 15% to ensure orders are accepted
        return 0.15
    except Exception as e:
        print(f"Failed to get max price deviation for {product_id}: {e}")
        return 0.15  # Conservative default

def log_order(crypto, order_type, price, base_size, usdc_amount, adjustment, order_response):
    """Log order details for tracking"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle response based on Coinbase API response format
    success = isinstance(order_response, dict) and order_response.get('success', False)
    status = "SUCCESS" if success else "FAILED"
    
    # Extract order details from success_response if available
    order_id = order_response.get('success_response', {}).get('order_id', 'N/A') if success else 'N/A'
    error = str(order_response) if not success else 'N/A'
    
    print(f"\n{timestamp} | {status} | {crypto}-USDC")
    print(f"Type: {order_type}")
    print(f"Price: {price} USDC")
    print(f"Size: {base_size} {crypto}")
    print(f"Total: {usdc_amount} USDC")
    print(f"Drop: {adjustment*100:.1f}%")
    print(f"Order ID: {order_id}")
    if not success:
        print(f"Error: {error}")
    print("-" * 50)
    return success

def calculate_ladder_steps(target_adjustment, max_deviation):
    """Calculate optimal ladder steps for order placement"""
    if target_adjustment <= max_deviation:
        return [(target_adjustment, 1.0)]
    
    # For larger drops, create a geometric progression of steps
    num_steps = min(5, math.ceil(target_adjustment / max_deviation))
    step_ratio = math.pow(target_adjustment / max_deviation, 1.0 / (num_steps - 1))
    
    steps = []
    for i in range(num_steps):
        adjustment = min(max_deviation * math.pow(step_ratio, i), target_adjustment)
        # Allocate more funds to lower price points
        weight = 1.0 + (i * 0.5)  # Increase weight for lower prices
        steps.append((adjustment, weight))
    
    # Normalize weights
    total_weight = sum(w for _, w in steps)
    return [(adj, w/total_weight) for adj, w in steps]

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
        
        try:
            product = client.get_product(product_id)
            price = float(product["price"])
            precision = get_precision(crypto)
            price_precision = get_price_precision(crypto)
            
            # Calculate ladder steps and weights
            steps = calculate_ladder_steps(target_price_adjustment, max_deviation)
            
            for current_adjustment, weight in steps:
                try:
                    # Calculate allocation with weight
                    allocation_amount = investment_amount * allocations[crypto] * weight
                    base_size = round(allocation_amount / price, precision)
                    limit_price = round(price * (1 - current_adjustment), price_precision)

                    if base_size > 0:
                        order_type = "LADDER" if len(steps) > 1 else "SINGLE"
                        order_id = f"adj_{current_adjustment:.2f}_{uuid.uuid4()}"
                        
                        order = client.limit_order_gtc_buy(
                            client_order_id=order_id,
                            product_id=product_id,
                            base_size=str(base_size),
                            limit_price=str(limit_price)
                        )
                        
                        success = log_order(crypto, order_type, limit_price, base_size, 
                                         allocation_amount, current_adjustment, order)
                        
                        if success:
                            total_usdc_deployed += allocation_amount
                        
                        time.sleep(1)  # Rate limiting delay
                except Exception as e:
                    print(f"Failed to place order for {crypto}-USDC at {current_adjustment*100:.1f}% drop: {e}")
        except Exception as e:
            print(f"Failed to process {crypto}-USDC: {e}")
    
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

    # Optimized order configurations with more conservative drops
    order_configs = [
        {'investment_amount': 300, 'price_adjustment': 0.60},  # 60% drop - creates ladder
        {'investment_amount': 250, 'price_adjustment': 0.45},  # 45% drop - creates ladder
        {'investment_amount': 200, 'price_adjustment': 0.30},  # 30% drop - creates ladder
        {'investment_amount': 100, 'price_adjustment': 0.20},  # 20% drop - creates ladder
        {'investment_amount': 75, 'price_adjustment': 0.15},   # 15% drop - single order
        {'investment_amount': 50, 'price_adjustment': 0.10},   # 10% drop - single order
        {'investment_amount': 15, 'price_adjustment': 0.05},   # 5% drop - single order
        {'investment_amount': 10, 'price_adjustment': 0.02},   # 2% drop - single order
    ]

    print("\nStarting DCA order placement...")
    print(f"Maximum USDC deployment per run: {1000} USDC")
    print("-" * 50)

    total_usdc_deployed = 0
    for config in order_configs:
        print(f"\nProcessing orders for {config['price_adjustment']*100:.1f}% price drop...")
        deployed = place_orders(client, cryptocurrencies, allocations, config['investment_amount'], 
                              config['price_adjustment'], total_usdc_deployed)
        total_usdc_deployed += deployed
        if total_usdc_deployed >= 1000:
            print("\nReached maximum USDC deployment limit")
            break

    print(f"\nOrder placement complete")
    print(f"Total USDC deployed: {total_usdc_deployed:.2f}")
    print(f"Remaining USDC capacity: {1000 - total_usdc_deployed:.2f}")

if __name__ == "__main__":
    main()