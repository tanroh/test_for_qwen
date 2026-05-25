import streamlit as st
import requests
import os
import pandas as pd
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="7-Day Weather Forecast",
    page_icon="🌤️",
    layout="wide"
)

# Title and description
st.title("🌤️ 7-Day Weather Forecast")
st.markdown("Select a city from presets or enter your own location")

# Preset locations with coordinates
preset_locations = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Moscow": {"lat": 55.7558, "lon": 37.6173}
}

# API configuration - get from Streamlit secrets
# API_KEY = st.secrets.get("OPENWEATHER_API_KEY", None)
API_KEY = os.environ.get("OPENWEATHER_API_KEY", None)

if not API_KEY:
    # Try alternative method for accessing secrets
    try:
        API_KEY = st.secrets["OPENWEATHER_API_KEY"]
    except Exception as e:
        API_KEY = "YOUR_API_KEY_HERE"

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Function to fetch weather data with better error handling and caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_weather_data(city):
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'  # For Celsius
        }
        
        response = requests.get(BASE_URL, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Authentication failed. Please check your OpenWeatherMap API key.")
            st.error("You can get a free API key at: https://openweathermap.org/api")
            return None
        else:
            try:
                error_data = response.json()
                st.error(f"Error {response.status_code}: {error_data.get('message', 'Unknown error')}")
            except:
                st.error(f"Error {response.status_code}: Failed to fetch weather data")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error occurred: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

# Function to process forecast data efficiently using pandas
def process_forecast_data(raw_data):
    if not raw_data or 'list' not in raw_data:
        return pd.DataFrame()
    
    # Efficiently create DataFrame from all data at once instead of appending
    processed_data = []
    for item in raw_data['list']:
        dt = datetime.fromtimestamp(item['dt'])
        processed_data.append({
            'datetime': dt,
            'temp': round(item['main']['temp'], 1),
            'feels_like': round(item['main']['feels_like'], 1),
            'humidity': item['main']['humidity'],
            'pressure': item['main']['pressure'],
            'description': item['weather'][0]['description'].title(),
            'wind_speed': item['wind']['speed']
        })
    
    # Create DataFrame once, not for each row
    return pd.DataFrame(processed_data)

# Sidebar with preset location buttons
st.sidebar.header("📍 Quick Locations")
selected_location = None

# Create buttons for preset locations
for location in preset_locations:
    if st.sidebar.button(location):
        selected_location = location

# Manual city input
st.sidebar.markdown("---")
city_input = st.sidebar.text_input("Enter City Name", value="")

# Handle selection
if selected_location:
    city = selected_location
elif city_input:
    city = city_input
else:
    # Default to London if no selection made
    city = "London"

# Show current location and fetch data
st.subheader(f"Weather in {city}")
with st.spinner("Fetching weather data..."):
    raw_data = get_weather_data(city)
    
if raw_data:
    df = process_forecast_data(raw_data)
    
    # Display general info with better formatting using pandas for calculations
    current_weather = raw_data['list'][0]['main']
    current_desc = raw_data['list'][0]['weather'][0]['description'].title()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Temperature", f"{current_weather['temp']}°C")
    with col2:
        st.metric("Humidity", f"{current_weather['humidity']}%")
    with col3:
        st.metric("Wind Speed", f"{raw_data['list'][0]['wind']['speed']} m/s")
    
    # Show map for selected location
    if city in preset_locations:
        location_info = preset_locations[city]
        map_data = pd.DataFrame({
            'lat': [location_info['lat']],
            'lon': [location_info['lon']]
        })
        
        st.subheader("📍 Location on Map")
        st.map(map_data)
    
    # Show 5-day forecast using pandas DataFrame for better display
    st.subheader("📅 5-Day Forecast")
    if not df.empty:
        # Use pandas styling options for better table presentation
        styled_df = df[['datetime', 'temp', 'feels_like', 'humidity', 'description']].style.format({
            'temp': '{:.1f}°C',
            'feels_like': '{:.1f}°C',
            'humidity': '{}%',
            'wind_speed': '{:.1f} m/s'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.warning("No forecast data available.")
else:
    st.error("Could not fetch weather data. Please check the city name or your API key.")

# Instructions for the user
st.markdown("---")
st.info("**Note**: This app uses OpenWeatherMap API. To get your own API key, visit [https://openweathermap.org/api](https://openweathermap.org/api)")
if API_KEY == "YOUR_API_KEY_HERE":
    st.warning("⚠️ Please replace 'YOUR_API_KEY_HERE' with your actual OpenWeatherMap API key in the code or in Streamlit secrets.")
