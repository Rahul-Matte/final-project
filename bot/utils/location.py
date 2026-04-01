import requests

import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def get_live_location():
    """
    Fetches the user's live location based on their public IP address.
    Returns a dictionary with 'city', 'region', 'lat', 'lon' or None if failed.
    """
    try:
        # Using ipapi.co (Free, HTTPS, JSON)
        headers = {"User-Agent": "AI-Farmer-Advisor/1.0"}
        response = requests.get("https://ipapi.co/json/", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"), # State
                "lat": float(data.get("latitude", 0)),
                "lon": float(data.get("longitude", 0))
            }
        else:
            print(f"Location API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Location Fetch Error: {e}")
        return None
