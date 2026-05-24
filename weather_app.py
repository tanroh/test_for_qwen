import streamlit as st
import requests
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
st.markdown("Enter a city name to get the current weather and 7-day forecast.")

# API configuration (using OpenWeatherMap free tier)
API_KEY = "9106e00acbe0c72f0d04e9f21c4bf5c8"
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Function to fetch weather data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_weather_data(city):
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'  # For Celsius
        }
        
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if response.status_code == 200:
            return data
        else:
            st.error(f"Error: {data.get('message', 'Failed to fetch weather data')}")
            return None
            
    except Exception as e:
        st.error(f"An error occurred while fetching data: {str(e)}")
        return None

# Function to process forecast data
def process_forecast_data(raw_data):
    if not raw_data or 'list' not in raw_data:
        return pd.DataFrame()
    
    # Extract relevant information for each 3-hour forecast
    processed_data = []
    
    for item in raw_data['list']:
        dt = datetime.fromtimestamp(item['dt'])
        
        processed_item = {
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M'),
            'temperature': round(item['main']['temp'], 1),
            'feels_like': round(item['main']['feels_like'], 1),
            'humidity': item['main']['humidity'],
            'pressure': item['main']['pressure'],
            'description': item['weather'][0]['description'].title(),
            'wind_speed': item['wind']['speed']
        }
        
        processed_data.append(processed_item)
    
    # Create DataFrame and group by date for 7-day forecast
    df = pd.DataFrame(processed_data)
    
    # For 7-day view, we'll show the average temperature per day 
    daily_avg = df.groupby('date').agg({
        'temperature': 'mean',
        'feels_like': 'mean',
        'humidity': 'mean',
        'pressure': 'mean',
        'wind_speed': 'mean'
    }).round(1)
    
    # Get the weather description for each day (first entry)
    daily_desc = df.groupby('date').first()['description'].reset_index()
    
    return df, daily_avg, daily_desc

# City input
city = st.text_input("Enter city name:", "London")

if city:
    with st.spinner(f"Fetching weather data for {city}..."):
        raw_data = get_weather_data(city)
        
        if raw_data:
            # Process the data
            df_full, df_daily_avg, df_daily_desc = process_forecast_data(raw_data)
            
            # Display current location info
            st.subheader(f"Weather in {raw_data['city']['name']}, {raw_data['city']['country']}")
            
            # Current weather display (first entry)
            current_weather = raw_data['list'][0]['main']
            current_desc = raw_data['list'][0]['weather'][0]['description'].title()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Temperature", f"{current_weather['temp']}°C")
            with col2:
                st.metric("Feels Like", f"{current_weather['feels_like']}°C")
            with col3:
                st.metric("Humidity", f"{current_weather['humidity']}%")
            with col4:
                st.metric("Wind Speed", f"{raw_data['list'][0]['wind']['speed']} m/s")
            
            # 7-day forecast
            st.subheader("7-Day Forecast")
            
            if not df_daily_avg.empty and not df_daily_desc.empty:
                # Create a simple bar chart for daily temperatures
                st.bar_chart(df_daily_avg['temperature'])
                
                # Show detailed daily data
                daily_data = pd.concat([df_daily_desc, df_daily_avg], axis=1)
                st.dataframe(daily_data.set_index('date'))
            else:
                st.write("No forecast data available.")
            
            # Raw 3-hour forecasts (optional toggle)
            if st.checkbox("Show detailed 3-hour forecasts"):
                st.subheader("Detailed Hourly Forecast")
                st.dataframe(df_full[['date', 'time', 'temperature', 'humidity', 'description']].reset_index(drop=True))

# Instructions for the user
st.markdown("---")
st.info("**Note**: This app uses OpenWeatherMap API. To get your own API key, visit [https://openweathermap.org/api](https://openweathermap.org/api) and sign up for a free account.")
