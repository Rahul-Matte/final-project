import requests
import time
from math import radians, sin, cos, sqrt, atan2
import streamlit as st
import json
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# User Agent is required for Nominatim
HEADERS = {
    "User-Agent": "AI-Farmer-Advisor/1.0"
}

# Load Mandi Coordinates from JSON
try:
    with open("assets/mandi_coords.json", "r") as f:
        MANDI_COORDS = json.load(f)
except FileNotFoundError:
    MANDI_COORDS = {}

# Fallback State Mandis if JSON is missing or incomplete
STATE_MANDIS_FALLBACK = {
    "Andhra Pradesh": [
        "Bapatla", "Tenali", "Guntur", "Vijayawada", "Ongole", "Nellore"
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"
    ],
    "Maharashtra": [
        "Pune", "Nashik", "Nagpur", "Mumbai", "Aurangabad"
    ],
    "Karnataka": [
        "Bangalore", "Mysore", "Hubli", "Mangalore"
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Trichy"
    ]
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_lat_lon(place):
    """
    Geocodes a place name to obtain latitude and longitude using geopy (Nominatim).
    """
    try:
        geolocator = Nominatim(user_agent="ai_farmer_advisor")
        location = geolocator.geocode(place, timeout=10)
        
        if location:
            return location.latitude, location.longitude
        return None, None

    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None, None


@st.cache_data(ttl=3600, show_spinner=False)
def reverse_geocode(lat, lon):
    """
    Converts lat/lon to address details using Nominatim.
    Returns: {"city": str, "state": str, "display_name": str} or None
    """
    try:
        geolocator = Nominatim(user_agent="ai_farmer_advisor")
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        
        if not location:
            return None
            
        address = location.raw.get("address", {})
        # Extract City/Town/Village
        city = address.get("city") or address.get("town") or address.get("village") or address.get("county") or "Unknown"
        state = address.get("state", "Unknown")
        
        return {
            "city": city,
            "state": state,
            "display_name": location.address
        }

    except Exception as e:
        print(f"Reverse Geocoding Error: {e}")
        return None


def calc_distance(lat1, lon1, lat2, lon2):
    """
    Calculates Haversine distance between two points in kilometers.
    """
    R = 6371 # Earth radius in km

    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except ValueError:
        return float('inf')

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


@st.cache_data(ttl=3600, show_spinner=False)
def get_all_mandi_routes(user_location, state):
    """
    Finds routes to all mandis in the given state from the user's location.
    Returns a list of dictionaries with mandi details, distance, and map link.
    """
    # 1. Try JSON DB first
    mandis_in_state = MANDI_COORDS.get(state, {})
    mandi_names = list(mandis_in_state.keys())
    
    # 2. Fallback
    if not mandi_names:
        mandi_names = STATE_MANDIS_FALLBACK.get(state, [])

    if not mandi_names:
        return []

    # Geocode user location
    u_lat, u_lon = get_lat_lon(f"{user_location}, {state}, India")

    if not u_lat:
        print(f"Could not find location: {user_location}")
        return []

    return get_mandi_routes_by_coords(u_lat, u_lon, state, radius_km=None) # No limit for general view


@st.cache_data(ttl=3600, show_spinner=False)
def get_mandi_routes_by_coords(u_lat, u_lon, state, radius_km=100):
    """
    Finds routes to mandis in the state using exact user coordinates.
    Optionally filters by radius_km.
    """
    # 1. Try JSON DB first
    mandis_in_state = MANDI_COORDS.get(state, {})
    
    # 2. Add fallback mandis if not in JSON
    fallback_list = STATE_MANDIS_FALLBACK.get(state, [])
    
    # Prepare list of candidates (name, lat, lon)
    candidates = []
    
    # Add from JSON
    for m_name, coords in mandis_in_state.items():
        candidates.append({"name": m_name, "lat": coords["lat"], "lon": coords["lon"]})

    # Add from Fallback (if not already present)
    existing_names = set(mandis_in_state.keys())
    for m_name in fallback_list:
        if m_name not in existing_names:
            # Need to geocode on fly
            query = f"{m_name}, {state}, India"
            m_lat, m_lon = get_lat_lon(query)
            if m_lat:
                candidates.append({"name": m_name, "lat": m_lat, "lon": m_lon})

    if not candidates:
        return []

    result = []

    for mandi in candidates:
        dist = calc_distance(u_lat, u_lon, mandi["lat"], mandi["lon"])

        # Filter by radius if specified
        if radius_km and dist > radius_km:
            continue

        # Google Maps Direction Link
        link = f"https://www.google.com/maps/dir/?api=1&origin={u_lat},{u_lon}&destination={mandi['lat']},{mandi['lon']}&travelmode=driving"

        result.append({
            "name": mandi["name"],
            "distance": round(dist, 2),
            "map": link,
            "lat": mandi["lat"],
            "lon": mandi["lon"]
        })

    # Sort by distance
    result.sort(key=lambda x: x["distance"])
    
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def get_nearby_cold_storage(user_location, state):
    """
    Searches for nearby cold storage using Nominatim and returns the nearest one.
    """
    u_lat, u_lon = get_lat_lon(f"{user_location}, {state}, India")
    
    if not u_lat:
        return None

    return get_nearby_cold_storage_by_coords(u_lat, u_lon, user_location, state)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cold_storage_routes_by_coords(u_lat, u_lon, city_hint=None, state_hint=None, radius_km=100):
    """
    Returns a list of cold storages near coordinates using Viewbox search.
    """
    try:
        geolocator = Nominatim(user_agent="ai_farmer_advisor")
        
        # Calculate Viewbox (Approx 100km ~ 1.0 degree)
        # 1 deg lat = 111km. 1 deg lon = 111km * cos(lat). Assuming 1.0 is safe enough buffer.
        offset = 1.0 
        viewbox = [
            (u_lat - offset, u_lon - offset), # Point 1
            (u_lat + offset, u_lon + offset)  # Point 2
        ]
        
        # Search 1: Generic "Cold Storage" within viewbox
        # Note: Nominatim viewbox expects (Point1, Point2) or list of Points.
        # bounded=True restricts results to this area.
        locations = geolocator.geocode("Cold Storage", exactly_one=False, limit=20, timeout=10, viewbox=viewbox)
        
        is_fallback = False
        if not locations:
             # Search 2: Try broader "Warehouse" if Cold Storage not found? 
             # Or Fallback to State-based query (which might be far)
             query = f"Cold Storage in {state_hint}" if state_hint else "Cold Storage India"
             locations = geolocator.geocode(query, exactly_one=False, limit=20, timeout=10)
             is_fallback = True

        if not locations:
             return []
             
        results = []
        
        for loc in locations:
            dist = calc_distance(u_lat, u_lon, loc.latitude, loc.longitude)
            
            # If fallback, we might get very far results. Filter strictly if user wants "nearby".
            # But let's show up to 200km if fallback?
            threshold = radius_km if not is_fallback else radius_km * 2
            
            if dist <= threshold:
                results.append({
                    "name": loc.address.split(",")[0],  # Short name
                    "full_address": loc.address,
                    "distance": round(dist, 1),
                    "map": f"https://www.google.com/maps/dir/?api=1&origin={u_lat},{u_lon}&destination={loc.latitude},{loc.longitude}&travelmode=driving"
                })
        
        # Sort by distance
        results.sort(key=lambda x: x["distance"])
        return results

    except Exception as e:
        print(f"Cold Storage Error: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_nearby_cold_storage_by_coords(u_lat, u_lon, city_hint=None, state_hint=None):
    """
    Wrapper to get just the nearest one (backward compatibility)
    """
    all_cs = get_cold_storage_routes_by_coords(u_lat, u_lon, city_hint, state_hint, radius_km=500)
    return all_cs[0] if all_cs else None
