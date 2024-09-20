import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta
from google.transit import gtfs_realtime_pb2
import requests


GTFS_STATIC_PATH = "GTFS_transit_static/"

# Load GTFS static data
stops_df = pd.read_csv(GTFS_STATIC_PATH + 'stops.txt')
routes_df = pd.read_csv(GTFS_STATIC_PATH + 'routes.txt')
trips_df = pd.read_csv(GTFS_STATIC_PATH + 'trips.txt')
stop_times_df = pd.read_csv(GTFS_STATIC_PATH + 'stop_times.txt')

# Display DataFrames to ensure they are loaded correctly
st.subheader("Stops Data")
st.write("stops_df: Contains information about all transit stops (station names, latitude, longitude, etc.)")
st.dataframe(stops_df.head())

st.subheader("Routes Data")
st.write("routes_df: Contains information about all transit routes (route names, colors, etc.)")
st.dataframe(routes_df.head())

st.subheader("Trips Data")
st.write("trips_df: Contains information about all transit trips (trip IDs, route IDs, etc.)")
st.dataframe(trips_df.head())

st.subheader("Stop Times Data")
st.write("stop_times_df: Contains information about all stop times for each trip.")
st.dataframe(stop_times_df.head())

# Select route from dropdown
route_id = st.selectbox("Select Route", routes_df['route_short_name'].unique())

# Find trips associated with the selected route
selected_route_id = routes_df[routes_df['route_short_name'] == route_id]['route_id'].values[0]
trips_for_route = trips_df[trips_df['route_id'] == selected_route_id]

# Get stop times for the selected trips
trip_ids = trips_for_route['trip_id'].unique()
stops_for_route = stop_times_df[stop_times_df['trip_id'].isin(trip_ids)]

# Merge with stops data to get stop names and locations
stops_for_route = stops_for_route.merge(stops_df, on='stop_id', how='left')

# Retrieve the route color from routes.txt (use a default color if not found)
route_color = routes_df[routes_df['route_id'] == selected_route_id]['route_color'].values
if len(route_color) > 0:
    route_color = "#" + route_color[0]  # Add '#' to make it a valid hex color
else:
    route_color = "#3388ff"  # Default color (blue) if no route color is provided

# Debugging: Print number of stops
num_stops = len(stops_for_route)
st.write(f"Number of stops for selected route: {num_stops}")

# Display the stops for the selected route
st.subheader(f"Stops for Route {route_id}")
st.dataframe(stops_for_route[['stop_name', 'stop_lat', 'stop_lon']].drop_duplicates())

# Limit number of stops to display (for performance testing)
stops_for_route_limited = stops_for_route[['stop_name', 'stop_lat', 'stop_lon']].drop_duplicates().head(50)

# Function to plot stops on a map using CircleMarker
def plot_stops_on_map(stops, route_color):
    nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=12)

    # Add CircleMarker for each stop
    for index, stop in stops.iterrows():
        folium.CircleMarker(
            location=[stop['stop_lat'], stop['stop_lon']],
            radius=6,  # Circle size
            color=route_color,  # Circle color matching the route color
            fill=True,
            fill_color=route_color,
            fill_opacity=0.7,
            popup=stop['stop_name']
        ).add_to(nyc_map)

    return nyc_map

# Display map of stops for the selected route
stops_map = plot_stops_on_map(stops_for_route[['stop_name', 'stop_lat', 'stop_lon']].drop_duplicates(), route_color)
st_folium(stops_map)


# Real time F train location


# MTA GTFS URL for BDFM lines, including the F train
MTA_GTFS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"

# Function to fetch real-time GTFS data
def fetch_real_time_data():
    try:
        response = requests.get(MTA_GTFS_URL)
        if response.status_code == 200:
            st.write("Successfully fetched data from the API")
            return response.content
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Function to parse the real-time GTFS data
def parse_gtfs_realtime_data(data):
    try:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(data)
        st.write("Successfully parsed GTFS feed")
        return feed
    except Exception as e:
        st.error(f"Error parsing GTFS data: {str(e)}")
        return None

# Function to convert Unix timestamp to NYC EST time
def convert_unix_time(unix_time):
    utc_time = datetime.fromtimestamp(unix_time, tz=timezone.utc)
    nyc_time = utc_time + timedelta(hours=-4)  # Adjust for EDT (-4 hours)
    return nyc_time.strftime('%Y-%m-%d %H:%M:%S')

# Function to track the current position of F trains
def get_f_train_position(feed, stops_df):
    f_train_positions = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):  
            trip = entity.vehicle.trip
            if trip.route_id == 'F':  # Only focus on F train data
                stop_id = entity.vehicle.stop_id
                timestamp = entity.vehicle.timestamp
                current_position = entity.vehicle.position

                # Get stop name from stops_df using stop_id
                if stop_id in stops_df['stop_id'].values:
                    stop_name = stops_df[stops_df['stop_id'] == stop_id]['stop_name'].values[0]
                else:
                    stop_name = "Unknown Stop"

                # Store train position and stop info
                f_train_positions.append({
                    "Train ID": trip.trip_id,
                    "Current Stop": stop_name,
                    "Stop ID": stop_id,
                    "Latitude": current_position.latitude if current_position.HasField('latitude') else 0,
                    "Longitude": current_position.longitude if current_position.HasField('longitude') else 0,
                    "Timestamp": convert_unix_time(timestamp)
                })

                # Debug: Show train position in Streamlit
                #st.write(f"F Train ID: {trip.trip_id}, Current Stop: {stop_name}, Latitude: {current_position.latitude}, Longitude: {current_position.longitude}, Timestamp: {convert_unix_time(timestamp)}")

    return pd.DataFrame(f_train_positions)

# Function to separate F trains by direction (northbound and southbound)
def separate_trains_by_direction(f_train_positions_df):
    northbound_trains = f_train_positions_df[f_train_positions_df['Train ID'].str.contains('N')]
    southbound_trains = f_train_positions_df[f_train_positions_df['Train ID'].str.contains('S')]
    return northbound_trains, southbound_trains

# Main Flow
st.subheader("Fetching Real-Time F Train Data")

# Fetch real-time data
real_time_data = fetch_real_time_data()

# Parse GTFS data
if real_time_data:
    gtfs_feed = parse_gtfs_realtime_data(real_time_data)

    #stops_df = pd.read_csv('stops.txt')  

    if gtfs_feed:
        # Track F train positions
        f_train_positions = get_f_train_position(gtfs_feed, stops_df)

        if not f_train_positions.empty:
            #Separate trains by direction (northbound vs southbound)
            northbound_trains, southbound_trains = separate_trains_by_direction(f_train_positions)

            # Sort by the most recent timestamp
            northbound_trains = northbound_trains.sort_values(by='Timestamp', ascending=True)
            southbound_trains = southbound_trains.sort_values(by='Timestamp', ascending=True)
            # Display tables for northbound and southbound F trains
            st.subheader("Northbound F Trains to Jamaica-179 St")
            st.dataframe(northbound_trains[['Train ID', 'Current Stop', 'Timestamp']])

            st.subheader("Southbound F Trains to Coney Island-Stillwell Av")
            st.dataframe(southbound_trains[['Train ID', 'Current Stop', 'Timestamp']])
        else:
            st.write("No F trains found.")