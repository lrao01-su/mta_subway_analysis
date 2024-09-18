import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone
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

#Real Time F Train Status at Roosevelt Island

# Define the real-time API URL (use the correct feed for the F train)
MTA_GTFS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"

# Function to fetch real-time GTFS data
def fetch_real_time_data():
    response = requests.get(MTA_GTFS_URL)
    if response.status_code == 200:
        return response.content
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return None

# Function to parse the real-time GTFS data
def parse_gtfs_realtime_data(data):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(data)
    return feed

# Filter the stops_df to find the stop ID for Roosevelt Island
roosevelt_island_stop = stops_df[stops_df['stop_name'].str.contains("Roosevelt Island", case=False)]
roosevelt_island_stop_id = roosevelt_island_stop['stop_id'].values[0]  # Extract the stop ID
st.write(f"Roosevelt Island Stop ID: {roosevelt_island_stop_id}")

# Function to filter F train status and calculate time remaining for arrival
def get_f_train_status(feed, roosevelt_stop_id, time_limit=30):
    f_train_status = []
    current_time = datetime.now(timezone.utc)

    for entity in feed.entity:
        if entity.trip_update:  # trip_update contains the trip status
            trip = entity.trip_update.trip

            # Only look for the F train
            if trip.route_id == 'F':
                for stop_time_update in entity.trip_update.stop_time_update:
                    # Check if the stop is Roosevelt Island
                    if stop_time_update.stop_id == roosevelt_stop_id:
                        # Get the arrival and departure times
                        arrival_timestamp = stop_time_update.arrival.time
                        arrival_time = datetime.fromtimestamp(arrival_timestamp, tz=timezone.utc)
                        minutes_until_arrival = (arrival_time - current_time).total_seconds() / 60
                        
                        # Only include trains arriving within the next 30 minutes
                        if 0 <= minutes_until_arrival <= time_limit:
                            f_train_status.append({
                                "Train ID": trip.trip_id,
                                "Route": trip.route_id,
                                "Arrival Time": arrival_time.strftime('%H:%M:%S'),
                                "Minutes Until Arrival": max(0, int(minutes_until_arrival))  # Avoid negative minutes
                            })

    return pd.DataFrame(f_train_status)


# Display map if route is selected
st.subheader(f"Map of Stops for Route {route_id}")
stops_map = plot_stops_on_map(stops_for_route_limited, route_color)
st_folium(stops_map)


# Display real-time train status at Roosevelt Island
st.subheader("F Train Status at Roosevelt Island")

# Fetch real-time GTFS data
real_time_data = fetch_real_time_data()

if real_time_data:
    # Parse the real-time GTFS data
    gtfs_feed = parse_gtfs_realtime_data(real_time_data)
    
    # Get the F train status at Roosevelt Island
    f_train_status_df = get_f_train_status(gtfs_feed, roosevelt_island_stop_id)
    
    if not f_train_status_df.empty:
        for index, row in f_train_status_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="Train ID", value=row['Train ID'])
                
                with col2:
                    st.metric(label="Arrives In", value=f"{row['Minutes Until Arrival']} mins")
                
                with col3:
                    st.metric(label="Arrival Time", value=row['Arrival Time'])
    else:
        st.write("No F train approaching Roosevelt Island at this time.")
        