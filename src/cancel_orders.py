from coinbase.rest import RESTClient
import os
import time
import re
import argparse

def get_orders_to_cancel(client, product_id):
    """Retrieve all open orders for a product."""
    try:
        orders = client.get_orders(product_id=product_id, status='OPEN')
        return orders
    except Exception as e:
        print(f"Failed to get orders for {product_id}: {e}")
        return []

def get_price_adjustment_from_order_id(client_order_id):
    """Extract price adjustment from client_order_id."""
    try:
        # Match the pattern adj_X.XX_ where X.XX is the price adjustment
        match = re.match(r'adj_(0\.\d{2})_', client_order_id)
        if match:
            return float(match.group(1))
    except (ValueError, AttributeError):
        pass
    return None

def should_cancel_order(order):
    """Determine if an order should be canceled based on its stored price adjustment."""
    try:
        client_order_id = order.get('client_order_id', '')
        price_adjustment = get_price_adjustment_from_order_id(client_order_id)
        
        if price_adjustment is None:
            print(f"Could not determine price adjustment for order {client_order_id}")
            return False
        
        # Cancel orders with price adjustments of 5%, 15%, 30%, and 50%
        target_adjustments = [0.05, 0.15, 0.30, 0.50]
        
        # Allow for some small variance in the price adjustment (0.001%)
        for target in target_adjustments:
            if abs(price_adjustment - target) <= 0.0001:  # Much tighter tolerance since we're using stored values
                return True
        
        return False
    except Exception as e:
        print(f"Error checking order {order.get('client_order_id')}: {e}")
        return False

def main():
    api_key = os.getenv('COINBASE_API_KEY')
    api_secret = os.getenv('COINBASE_API_SECRET')

    client = RESTClient(api_key=api_key, api_secret=api_secret)
    
    cryptocurrencies = ['BTC', 'ETH', 'XRP', 'ONDO', 'LINK', 'AVAX', 'RNDR', 'SOL', 'ENS']
    
    for crypto in cryptocurrencies:
        product_id = f"{crypto}-USDC"
        print(f"\nProcessing {product_id}...")
        
        # Get all open orders
        orders = get_orders_to_cancel(client, product_id)
        
        # Process each order
        for order in orders:
            if should_cancel_order(order):
                try:
                    order_id = order.get('order_id')
                    client.cancel_orders(order_ids=[order_id])
                    print(f"Canceled order {order_id} for {product_id} (client_order_id: {order.get('client_order_id')})")
                    # Add small delay to avoid rate limiting
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Failed to cancel order {order.get('order_id')} for {product_id}: {e}")
        
        # Add delay between processing different cryptocurrencies
        time.sleep(1)

if __name__ == "__main__":
    main() 