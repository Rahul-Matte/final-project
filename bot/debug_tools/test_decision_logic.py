import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.decision import store_analysis

def test_storage_decision():
    print("--- Test: Storage Decision Logic ---")
    
    # Mock data
    mandis = [{"name": "Mandi A", "distance": 10, "map": "url"}]
    cost = 1000
    qty = 100
    
    # Scenario 1: Low Price
    print("\nScenario 1: Low Price (20)")
    price = 20
    days, date_str, future_price, profit, best_mandi, _ = store_analysis(price, qty, cost, mandis, "tomato")
    print(f"Result: Days={days}, Future Price={future_price}, Profit={profit}")
    
    # Scenario 2: High Price
    print("\nScenario 2: High Price (30)")
    price = 30
    days, date_str, future_price, profit, best_mandi, _ = store_analysis(price, qty, cost, mandis, "tomato")
    print(f"Result: Days={days}, Future Price={future_price}, Profit={profit}")

if __name__ == "__main__":
    test_storage_decision()
