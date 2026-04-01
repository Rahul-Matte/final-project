import requests

API_KEY = "7143901c56dc165a3d46291f25321eb9"

def get_weather_condition(city):
    """
    Fetches the current weather condition for the given city using OpenWeatherMap.
    """
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10)
        
        if r.status_code != 200:
             return "Not available"

        data = r.json()
        
        if "weather" in data:
            return data["weather"][0]["description"].title()
            
        return "Not available"

    except Exception:
        return "Not available"
