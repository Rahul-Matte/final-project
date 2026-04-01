from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

def test_cs_search(city, state):
    geolocator = Nominatim(user_agent="ai_farmer_advisor_debug")
    
    print(f"\n--- Testing for {city}, {state} ---")
    
    # 1. Geocode City Center
    loc = geolocator.geocode(f"{city}, {state}, India")
    if not loc:
        print("City Center not found!")
        return
        
    print(f"City Center: {loc.latitude}, {loc.longitude}")
    
    queries = [
        f"Cold Storage in {city}, {state}",
        f"Cold Storage, {city}, {state}",
        f"Warehouse in {city}, {state}",
        f"Cold Storage near {city}",
        "Cold Storage" # relying on viewbox? No, try simple query first
    ]
    
    for q in queries:
        try:
            print(f"Query: '{q}'")
            # For general query "Cold Storage", we might get random results if not bounded.
            # But let's see what Nominatim returns for specific queries.
            limit = 5
            res = geolocator.geocode(q, exactly_one=False, limit=limit)
            if res:
                print(f"  Found {len(res)} results:")
                for r in res:
                    print(f"    - {r.address} ({r.latitude}, {r.longitude})")
            else:
                print("  No results.")
            time.sleep(1) 
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_cs_search("Bapatla", "Andhra Pradesh")
    test_cs_search("Guntur", "Andhra Pradesh")
