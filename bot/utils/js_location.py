import streamlit as st
from streamlit_js_eval import get_geolocation

def get_browser_location():
    """
    Uses streamlit-js-eval to prompt the browser for location.
    Returns: {"coords": {"latitude": float, "longitude": float}, ...} or None
    """
    # This component renders a hidden hook to get location
    loc = get_geolocation()
    
    if loc and "coords" in loc:
        return {
            "lat": loc["coords"]["latitude"],
            "lon": loc["coords"]["longitude"]
        }
    return None
