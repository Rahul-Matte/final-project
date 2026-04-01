def transport_cost(distance, qty, rate=0.5):
    """
    Calculates transport cost based on distance, quantity, and rate (default 0.5/km).
    """
    return int(distance * qty * rate)


def calc_profit(price, qty, cost, distance, transport_rate=0.5):
    """
    Calculates net profit.
    Profit = (Price * Qty) - Cultivation Cost - Transport Cost
    """
    transport = transport_cost(distance, qty, transport_rate)
    total = price * qty
    profit = total - cost - transport
    return profit, transport


def best_mandi_profit(mandis, price_data, qty, cost, transport_rate=0.5):
    """
    Finds the mandi that yields the highest profit.
    price_data: Can be a float (legacy) or dict ({"average": float, "markets": {name: price}})
    """
    if not mandis:
        return None

    best = None
    
    # Handle legacy float price
    default_price = price_data if isinstance(price_data, (int, float)) else price_data.get("average", 0)
    market_prices = price_data.get("markets", {}) if isinstance(price_data, dict) else {}

    for m in mandis:
        # Determine price for this specific mandi
        # API Market names: "Madnapalle", "Palamaner"
        # Map Mandi names: "Madnapalle", "Palamaner" (usually match)
        # Try exact match or fuzzy match
        
        m_name = m["name"].title()
        current_price = default_price
        
        # Try to find specific price
        if m_name in market_prices:
            current_price = market_prices[m_name]
        else:
            # Simple substring match fallback
            for k, v in market_prices.items():
                if m_name in k or k in m_name:
                    current_price = v
                    break
        
        profit, transport = calc_profit(
            current_price, qty, cost, m["distance"], transport_rate
        )

        if not best or profit > best["profit"]:
            best = {
                "mandi": m["name"],
                "distance": m["distance"],
                "map": m["map"],
                "profit": profit,
                "transport": transport,
                "price": current_price, # Store the price used
                "net_profit": profit # Explicit field for strategy output
            }

    return best



# Approximate Shelf Life in Days (assuming standard conditions)
SHELF_LIFE = {
    "tomato": 10,
    "potato": 60,
    "onion": 90,
    "chilly": 20,
    "brinjal": 7,
    "okra": 5,
    "carrot": 15,
    "cabbage": 14,
    "mango": 10,
    "banana": 5
}

def get_shelf_life(crop):
    return SHELF_LIFE.get(crop.lower(), 7) # Default 7 days

def predict_price(price, days, total_shelf_life=10):
    """
    Realistic 3-phase price prediction model:
    - Phase 1 (0–40% of shelf life): +1.5%/day premium for fresh stored crop
    - Phase 2 (40–70% of shelf life): plateau, market equilibrium
    - Phase 3 (70–100% of shelf life): -3%/day as quality decays, forced sell pressure
    This produces a bell-curve profit roadmap rather than unlimited linear growth.
    """
    if total_shelf_life <= 0:
        return round(price, 2)

    ratio = days / total_shelf_life  # 0.0 → 1.0

    if ratio <= 0.4:
        # Phase 1: Early storage premium
        multiplier = 1 + (0.015 * days)
    elif ratio <= 0.7:
        # Phase 2: Plateau — price stabilises near peak
        peak_days = 0.4 * total_shelf_life
        peak_multiplier = 1 + (0.015 * peak_days)
        multiplier = peak_multiplier  # flat
    else:
        # Phase 3: Decay — quality loss drives price down
        peak_days = 0.4 * total_shelf_life
        peak_multiplier = 1 + (0.015 * peak_days)
        decay_days = days - (0.7 * total_shelf_life)
        multiplier = peak_multiplier * ((1 - 0.03) ** decay_days)

    return round(price * multiplier, 2)


from datetime import datetime, timedelta

def store_analysis(price, qty, cost, mandis, crop, days_since_harvest=0):
    """
    Analyzes profit if crop is stored.
    Finds the optimal number of days to store within the remaining shelf life.
    Returns: best_days, best_date_str, future_price, best_stored_profit, best_mandi_deal
    """
    base_price = price if isinstance(price, (int, float)) else price.get("average", 0)
    total_life = get_shelf_life(crop)
    remaining_life = max(0, total_life - days_since_harvest)
    
    if remaining_life <= 1:
        # Not enough life to store
        return 0, datetime.now().strftime("%d %b %Y"), base_price, 0, None, []

    best_stored_profit = float('-inf')
    best_days = 0
    best_mandi_deal = None
    final_future_price = base_price

    # Check potential profit for each day up to remaining life (capped at 30 days for safety)
    check_range = min(remaining_life, 30)
    
    daily_analysis = []

    for d in range(1, check_range + 1):
        # We need to predict future price. 
        # For simplicity, we apply prediction to the BASE average price, 
        # and assume individual market prices scale similarly.
        # Ideally, we'd predict for each market, but passing a complex dict to predict_price is overkill.
        
        current_day = d + days_since_harvest
        future_base_p = predict_price(base_price, current_day, total_shelf_life=total_life)
        
        # Reconstruct a "Future Price Data" object
        future_price_data = future_base_p
        
        if isinstance(price, dict):
            future_markets = {k: predict_price(v, current_day, total_shelf_life=total_life) for k, v in price.get("markets", {}).items()}
            future_price_data = {
                "average": future_base_p,
                "markets": future_markets
            }
        
        # Dynamic Storage Cost: 1% of current value per day (scales with price)
        # 0.01 * price * qty * days
        storage_cost = 0.01 * base_price * qty * d
        
        # Find best mandi at future price
        mandi_deal = best_mandi_profit(mandis, future_price_data, qty, cost)
        
        if mandi_deal:
            # Net profit after storage
            net_profit_stored = mandi_deal["profit"] - storage_cost
            
            # Store daily analysis
            day_date = datetime.now() + timedelta(days=d)
            daily_analysis.append({
                "Day": d,
                "Date": day_date.strftime("%d %b"),
                "Profit": int(net_profit_stored),
                "Price": future_base_p
            })
            
            if net_profit_stored > best_stored_profit:
                best_stored_profit = net_profit_stored
                best_days = d
                final_future_price = mandi_deal.get("price", future_base_p) # Use specific price if avail
                best_mandi_deal = mandi_deal

    # Calculate exact date
    best_date = datetime.now() + timedelta(days=best_days)
    best_date_str = best_date.strftime("%d %b %Y") # e.g., "25 Feb 2026"

    return best_days, best_date_str, final_future_price, best_stored_profit, best_mandi_deal, daily_analysis


def compare_profits(current_profit, stored_profit):
    """
    Returns True if stored profit is significantly better (>15% increase).
    """
    if current_profit <= 0:
        return True, 100 # If current is loss, any profit is better
    
    if stored_profit <= current_profit:
        return False, 0
    
    percent_inc = ((stored_profit - current_profit) / abs(current_profit)) * 100
    
    return percent_inc > 15, round(percent_inc, 1)

