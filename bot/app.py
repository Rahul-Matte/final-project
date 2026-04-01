import streamlit as st
import os

# ================== IMPORTS ==================
from utils.price_api import get_price
from utils.weather_api import get_weather_condition
from utils.maps_api import get_all_mandi_routes, get_nearby_cold_storage, get_mandi_routes_by_coords, get_nearby_cold_storage_by_coords, reverse_geocode
from utils.decision import best_mandi_profit, store_analysis, compare_profits
from utils.db import save_farmer

from utils.voice_out import speak_full, detect_lang
from utils.translator import translate
from models.freshness_model import check_freshness
from models.cv_model import analyze_image
from utils.localization import get_text
from utils.location import get_live_location
from streamlit_js_eval import get_geolocation

# ================== CONFIG ==================
st.set_page_config(
    page_title="AI Farmer Advisor",
    layout="wide",
    page_icon="🌾"
)

# ================== SESSION STATE ==================
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# Auto-detect location if not set
if "location" not in st.session_state:
    st.session_state.location = ""

if "coords" not in st.session_state:
     # Try to fetch live location once on startup
    live_loc = get_live_location()
    if live_loc:
        st.session_state.location = live_loc["city"]
        st.session_state.auto_city = live_loc["city"] # Track auto-detected name
        st.session_state.coords = {"lat": live_loc["lat"], "lon": live_loc["lon"]}
        
        # State matching logic
        detected_region = live_loc["region"]
        supported_states = ["Andhra Pradesh", "Telangana", "Maharashtra", "Karnataka", "Tamil Nadu"]
        found_state = None
        
        for s in supported_states:
            if s.lower() in detected_region.lower() or detected_region.lower() in s.lower():
                found_state = s
                break
        
        if not found_state:
             if "Andhra" in detected_region: found_state = "Andhra Pradesh"
             elif "Telangana" in detected_region: found_state = "Telangana"

        if found_state:
             st.session_state.state_idx = supported_states.index(found_state)
    else:
        st.session_state.auto_city = None


for key in ["crop", "location"]:
    if key not in st.session_state:
        st.session_state[key] = ""


# ================== SIDEBAR ==================
with st.sidebar:
    st.header(get_text("settings", st.session_state.lang))

    def change_lang():
        st.session_state.lang = st.session_state.lang_select

    st.selectbox(
        get_text("lang_select", st.session_state.lang),
        ["en", "hi", "te", "ta", "kn", "mr"],
        key="lang_select",
        on_change=change_lang
    )

# ================== TITLE ==================
st.markdown(
    f"<h1 style='text-align:center;'>{get_text('title', st.session_state.lang)}</h1>",
    unsafe_allow_html=True
)


# ================== MAIN FORM ==================

if 'page' not in st.session_state:
    st.session_state.page = 'input'

if st.session_state.page == 'input':
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(get_text("farmer_details", st.session_state.lang))

        supported_states = ["Andhra Pradesh", "Telangana", "Maharashtra", "Karnataka", "Tamil Nadu"]
        s_idx = st.session_state.get("state_idx", 0)

        # Text Input for Crop
        st.text_input(get_text("crop_name", st.session_state.lang), key="crop")
        
        # Location Row with Live Button
        loc_c1, loc_c2 = st.columns([0.7, 0.3])

        # Execute Button Logic FIRST (Right Column)
        with loc_c2:
            st.write("") # Spacer
            st.write("") 
            
            # Browser-based Geolocation Button
            loc_data = get_geolocation(component_key="get_loc")
            
            if loc_data and "coords" in loc_data:
                lat = loc_data["coords"]["latitude"]
                lon = loc_data["coords"]["longitude"]
                timestamp = loc_data.get("timestamp", 0)
                
                # Check if this is a new update to avoid loop
                if timestamp > st.session_state.get("geo_ts", 0):
                    st.session_state.geo_ts = timestamp
                    st.session_state.coords = {"lat": lat, "lon": lon}
                    
                    # Reverse Geocode to get City/State
                    with st.spinner("📍 Found coordinates! Getting address..."):
                        rev = reverse_geocode(lat, lon)
                        
                        if rev:
                            st.session_state.location = rev["city"]
                            st.session_state.auto_city = rev["city"] # Update auto tracker
                            
                            # Map State
                            detected_state = rev["state"]
                            supported_states = ["Andhra Pradesh", "Telangana", "Maharashtra", "Karnataka", "Tamil Nadu"]
                            found_state = None
                            
                            # Improved State Matching
                            for s in supported_states:
                                if s.lower() in detected_state.lower() or detected_state.lower() in s.lower():
                                    found_state = s
                                    break
                            
                            # Fallback for AP/Telangana variants
                            if not found_state:
                               if "Andhra" in detected_state: found_state = "Andhra Pradesh"
                               elif "Telangana" in detected_state: found_state = "Telangana"
                            
                            if found_state:
                                st.session_state.state_idx = supported_states.index(found_state)
                            
                            st.success(f"📍 {rev['city']}, {rev['state']}")
                            st.rerun()
                        else:
                            st.warning("📍 Coords found, but address lookup failed.")

        # Render Input Field SECOND (Left Column)
        with loc_c1:
             st.text_input(get_text("location", st.session_state.lang), key="location")
        
        st.selectbox(
            get_text("state", st.session_state.lang),
            supported_states,
            index=s_idx,
            key="state"
        )

        # Use unified mic_to_field for numbers too
        # Initialize defaults if not set
        if "quantity" not in st.session_state: st.session_state.quantity = 1
        if "cost" not in st.session_state: st.session_state.cost = 0
        if "days" not in st.session_state: st.session_state.days = 0

        st.number_input(get_text("quantity", st.session_state.lang), min_value=1, key="quantity", step=1)
        st.number_input(get_text("cost", st.session_state.lang), min_value=0, key="cost", step=1)
        st.number_input(get_text("days", st.session_state.lang), min_value=0, key="days", step=1)

    with col2:
        st.subheader(get_text("crop_image", st.session_state.lang))
        
        img_option = st.radio("Input Method", ["Camera", "Upload"], horizontal=True, label_visibility="collapsed")
        
        image_input = None
        if img_option == "Camera":
            image_input = st.camera_input(get_text("take_photo", st.session_state.lang), key="camera")
        else:
            image_input = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key="uploader")
        if image_input:
            st.session_state.kept_image = image_input

    # ================== ANALYZE ==================
        if st.button(get_text("analyze", st.session_state.lang), use_container_width=True):
            if not st.session_state.crop:
                st.error(get_text("error_req", st.session_state.lang))
            else:
                st.session_state.saved_crop = st.session_state.crop
                st.session_state.saved_location = st.session_state.location
                st.session_state.saved_lang = st.session_state.lang
                st.session_state.saved_qty = st.session_state.quantity
                st.session_state.saved_cost = st.session_state.cost
                st.session_state.saved_days = st.session_state.days
                st.session_state.saved_state = st.session_state.get("state", "Andhra Pradesh")
                
                st.session_state.page = 'results'
                st.rerun()

elif st.session_state.page == 'results':
    st.button("⬅️ " + (get_text("back", st.session_state.lang) if "back" in locals() else "Back"), on_click=lambda: st.session_state.update({'page': 'input'}))

    crop = st.session_state.saved_crop
    location = st.session_state.saved_location
    lang = st.session_state.saved_lang

    qty = st.session_state.saved_qty
    cost = st.session_state.saved_cost
    days = st.session_state.saved_days
    state = st.session_state.saved_state

    # Auto-detect location if not provided
    if not location:
        with st.spinner(get_text("analyzing", lang) + " (Detecting Location...)"):
            loc_data = get_live_location()
            if loc_data:
                location = loc_data["city"]
                st.session_state.location = location
                st.session_state.auto_city = location
                st.session_state.coords = {"lat": loc_data["lat"], "lon": loc_data["lon"]}
                
                # Update State automatically
                detected_region = loc_data["region"]
                supported_states = ["Andhra Pradesh", "Telangana", "Maharashtra", "Karnataka", "Tamil Nadu"]
                for s in supported_states:
                    if s.lower() in detected_region.lower() or detected_region.lower() in s.lower():
                        state = s
                        st.session_state.state_idx = supported_states.index(s)
                        break
                
                st.success(f"📍 Auto-detected: {location}, {state}")
            else:
                st.error("Could not detect location. Please enter manually.")
                st.stop()

    # ================== CACHE EXPENSIVE API CALLS ==================
    # Build a cache key from inputs. If inputs change (new Analyze click), cache is invalidated.
    cache_key = f"{crop}_{state}_{qty}_{cost}_{days}_{location}"
    
    if st.session_state.get('analysis_cache_key') != cache_key:
        # Clear old cache so it re-fetches
        st.session_state.pop('analysis_cache', None)
        st.session_state.analysis_cache_key = cache_key

    if 'analysis_cache' not in st.session_state:
        with st.spinner(get_text("analyzing", lang)):
        
            freshness, quality = "N/A", "N/A"
            image = st.session_state.get('kept_image')
            if image:
                if 'img_analysis' not in st.session_state or st.session_state.img_analysis.get('img') != image:
                    st.session_state.img_analysis = {
                        'img': image,
                        'freshness': check_freshness(image, days),
                        'quality': analyze_image(image)
                    }
                freshness = st.session_state.img_analysis['freshness']
                quality = st.session_state.img_analysis['quality']

            # Get full price data (Average + Per Market)
            from utils.price_api import get_market_prices
            price_data = get_market_prices(crop, state)
            
            # Invalid Crop Handling
            if isinstance(price_data, dict) and "error" in price_data:
                st.error(price_data["error"])
                st.stop()
            
            if price_data is None:
                 st.error(f"⚠️ Could not fetch market price for '{crop}' in '{state}'. Please check the crop name or try a generic name (e.g., 'Tomato' instead of 'Tomato Hybrid').")
                 st.stop()

            # Extract average for display default
            avg_price = price_data.get("average", 0)
            resolved_crop = price_data.get("crop_name", crop)
            
            # Display resolved crop name if fuzzy matched
            if resolved_crop.lower() != crop.lower():
                st.info(f"ℹ️ **Note:** Searched for '**{resolved_crop}**' instead of '{crop}'.")
                crop = resolved_crop

            # Location Logic: STRICT MANUAL PRIORITY
            target_lat, target_lon = None, None
            is_manual = location != st.session_state.get("auto_city")
            
            from utils.maps_api import get_lat_lon, get_mandi_routes_by_coords, get_all_mandi_routes, get_nearby_cold_storage_by_coords
            
            if is_manual:
                geo_lat, geo_lon = get_lat_lon(f"{location}, {state}, India")
                if geo_lat:
                    target_lat, target_lon = geo_lat, geo_lon
                    st.session_state.coords = {"lat": target_lat, "lon": target_lon}
                else:
                    target_lat = None
            else:
                if st.session_state.get("coords"):
                    target_lat = st.session_state.coords["lat"]
                    target_lon = st.session_state.coords["lon"]
            
            # Mandi/Coord Logic
            mandis = []
            best = None
            has_location_coords = False
            
            if target_lat:
                has_location_coords = True
                mandis = get_mandi_routes_by_coords(target_lat, target_lon, state)
            else:
                if is_manual:
                    st.warning(f"⚠️ Could not pinpoint exact location for '**{location}**'. Distance calculations and Map links will be disabled.")
            
            if has_location_coords and not mandis:
                st.warning(f"No mandis found within {state} for the given location.")

            if mandis:
                best = best_mandi_profit(mandis, price_data, qty, cost)
                weather = get_weather_condition(best["mandi"]) if best else "Unknown"
            else:
                best = None
                weather = "Unknown"

            # Check Cold Storage option
            rec_days, rec_date, future_price, stored_profit, best_stored, profit_roadmap = store_analysis(price_data, qty, cost, mandis, crop, days)
            
            should_store, profit_inc = compare_profits(best["profit"] if best else 0, stored_profit)
            decision = "STORE" if should_store else "SELL"
            
            save_farmer(crop, location, qty, cost)

            # STORE everything in cache
            st.session_state.analysis_cache = {
                'freshness': freshness, 'quality': quality,
                'price_data': price_data, 'avg_price': avg_price,
                'crop': crop, 'best': best, 'weather': weather,
                'has_location_coords': has_location_coords,
                'target_lat': target_lat, 'target_lon': target_lon,
                'mandis': mandis,
                'rec_days': rec_days, 'rec_date': rec_date,
                'future_price': future_price, 'stored_profit': stored_profit,
                'profit_roadmap': profit_roadmap,
                'should_store': should_store, 'profit_inc': profit_inc,
                'decision': decision,
            }

    # Restore from cache
    _c = st.session_state.analysis_cache
    freshness      = _c['freshness']
    quality        = _c['quality']
    price_data     = _c['price_data']
    avg_price      = _c['avg_price']
    crop           = _c['crop']
    best           = _c['best']
    weather        = _c['weather']
    has_location_coords = _c['has_location_coords']
    target_lat     = _c['target_lat']
    target_lon     = _c['target_lon']
    mandis         = _c['mandis']
    rec_days       = _c['rec_days']
    rec_date       = _c['rec_date']
    future_price   = _c['future_price']
    stored_profit  = _c['stored_profit']
    profit_roadmap = _c['profit_roadmap']
    should_store   = _c['should_store']
    profit_inc     = _c['profit_inc']
    decision       = _c['decision']

    # ================== OUTPUT ==================
    st.divider()
    st.subheader(get_text("results", lang))

    m1, m2, m3, m4 = st.columns(4)
    
    # Display the price used for the BEST mandi if available, else average
    display_price = avg_price
    if best and "price" in best:
        display_price = best["price"]
        
    m1.metric(get_text("price", lang), f"₹{display_price}/kg")
    
    # Translate freshness/qual values? keeping English specific values for now or could add to dict
    m2.metric(get_text("freshness", lang), freshness) 
    m3.metric(get_text("quality", lang), quality)
    
    current_profit_val = int(best['profit']) if best else 0
    m4.metric(get_text("profit", lang), f"₹{current_profit_val}")

    summary = (
        f"Freshness: {freshness}. "
        f"Quality: {quality}. "
        f"Recommended: {decision}. "
        f"Best Mandi: {best['mandi'] if best else 'N/A'}. "
        f"Price: ₹{display_price}/kg."
    )
    
    translated = translate(summary, st.session_state.lang)
    st.success(translated)
    
    # Display Validation Results
    st.info(f"✨ **Image Quality Check:** {quality}")

    # ================== NEW STRATEGY SECTION ==================
    # Only show if valid location coords were found
    if has_location_coords:
        st.divider()
        st.header(f"🚀 Market Strategy (100km Radius)")
        
        # Strategy Inputs
        strat_col1, strat_col2 = st.columns(2)
        with strat_col1:
            # User defined transport cost
            trans_cost_per_km = st.number_input("🚚 Transport Cost (₹/km)", min_value=0.0, value=2.0, step=0.5, format="%.2f")
        
        with strat_col2:
            st.write("") # Spacer

        # 1. Use the coordinates we resolved earlier (target_lat/lon)
        strat_lat, strat_lon = target_lat, target_lon
            
        # 2. Filter Mandis within 100km
        nearby_mandis = []
        if strat_lat:
            # Reuse logic
            nearby_mandis = get_mandi_routes_by_coords(strat_lat, strat_lon, state, radius_km=100)
        
        # 3. Calculate Profit for filtered mandis using Custom Transport Cost
        strategy_results = []
        
        market_prices = price_data.get("markets", {}) if isinstance(price_data, dict) else {}
        
        # Fallback price
        base_price = price_data if isinstance(price_data, (int, float)) else price_data.get("average", 0)

        if nearby_mandis:
            # Calculate for each nearby mandi
            for m in nearby_mandis:
                # Determine price (Exact or Average)
                m_price = base_price
                m_name = m["name"].title()
                
                # Key matching logic
                if m_name in market_prices:
                     m_price = market_prices[m_name]
                else:
                     for k, v in market_prices.items():
                        if m_name in k or k in m_name:
                            m_price = v
                            break
                
                t_cost = m["distance"] * trans_cost_per_km
                revenue = m_price * qty
                net_profit = revenue - cost - t_cost
                
                strategy_results.append({
                    "Mandi": m["name"],
                    "Distance (km)": m["distance"],
                    "Price (₹/kg)": round(m_price, 2),
                    "Revenue (₹)": int(revenue),
                    "Total Cost (₹)": int(cost + t_cost),
                    "Transport Cost (₹)": round(t_cost, 1),
                    "Net Profit (₹)": int(net_profit),
                    "Map": m["map"]
                })
            
            # Sort by Net Profit
            strategy_results.sort(key=lambda x: x["Net Profit (₹)"], reverse=True)
            
            # Display Top 5
            top_5 = strategy_results[:5]
            
            if top_5:
                # 1. Recommend Best
                best_strat = top_5[0]
                st.success(f"🏆 **Best Option:** **{best_strat['Mandi']}** (Profit: ₹{best_strat['Net Profit (₹)']})")
                st.markdown(f"📍 **[Navigate to {best_strat['Mandi']}]({best_strat['Map']})**")
                
                # 2. Table
                st.markdown("### 📋 Top 5 Profitable Mandis")
                # Create cleaner dict for display
                import pandas as pd
                df_display = pd.DataFrame(top_5).drop(columns=["Map"])
                st.table(df_display)
                
            else:
                st.warning("No profitable mandis found within 100km.")
                
    else:
        st.warning("No mandis found within 100km radius of your location.")
    
    # Fallback View: show Market Prices if NO location found or just as comprehensive info
    if price_data and isinstance(price_data, dict) and "markets" in price_data:
             with st.expander("📊 View All Market Prices (Statewide)"):
                  st.json(price_data["markets"])


    # Cold Storage Recommendation - Show Analysis Always if valid days
    if rec_days > 0:
        st.divider()
        st.subheader(f"❄️❄️ {get_text('cold_storage', lang)}")
        
        # Strategy Display
        display_future_price = 0
        try:
             if isinstance(future_price, (int, float)):
                 display_future_price = future_price
             elif isinstance(future_price, dict) or hasattr(future_price, "get"):
                 display_future_price = future_price.get("average", 0)
             else:
                 display_future_price = float(future_price)
        except:
            display_future_price = 0 

        if display_future_price and display_future_price != 0:
             st.success(f"📌 **Strategy:** Store until **{rec_date}** ({rec_days} days) -> to get approx **₹{display_future_price}/kg**. Est Profit: **₹{int(stored_profit)}**")
        else:
             st.warning(f"⚠️ Strategy data incomplete.")

        msg = get_text("cs_msg", lang).format(profit_diff=profit_inc)
        st.write(msg)
        
        # Cold Storage Search (Coords vs Text)
        cs_loc = None
        if has_location_coords:
             # Use the new Viewbox search logic
             from utils.maps_api import get_cold_storage_routes_by_coords
             all_cs = get_cold_storage_routes_by_coords(target_lat, target_lon, location, state, radius_km=100)
             if all_cs:
                 cs_loc = all_cs[0]
        else:
             # Fallback to pure text search
             try:
                from utils.maps_api import get_nearby_cold_storage
                cs_loc = get_nearby_cold_storage(location, state)
             except: cs_loc = None

        if cs_loc:
             st.write(f"🏭 **{get_text('nearest_cs', lang)}**: {cs_loc['name']} ({cs_loc['distance']} km)")
             st.markdown(f"📍 **[Navigate to {cs_loc['name']}]({cs_loc['map']})**")

        # Profit Roadmap Visualization
        if profit_roadmap:
            st.divider()
            st.markdown(f"### 📈 {get_text('profit_roadmap', lang) if 'profit_roadmap' in locals() else 'Profit Roadmap (Storage Analysis)'}")
            
            # Allow user to filter range
            max_days = len(profit_roadmap)
            days_to_show = st.slider("Forecast Days", min_value=1, max_value=max_days, value=min(7, max_days))
            
            # Filter data
            filtered_roadmap = profit_roadmap[:days_to_show]
            
            # Prepare data for chart
            chart_data = {item["Date"]: item["Profit"] for item in filtered_roadmap}
            st.bar_chart(chart_data)
            
            st.info(f"The chart shows how your profit changes if you store the crop for 1 to {days_to_show} days.")

    speak_full(translated, st.session_state.lang)
