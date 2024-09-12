import requests
import pandas as pd
import streamlit as st
import pydeck as pdk
from google.transit import gtfs_realtime_pb2
from datetime import datetime

# Replace with the path to your GTFS static data
GTFS_STATIC_PATH = "GTFS_transit_static/"

# Load GTFS static data
stops_df = pd.read_csv(GTFS_STATIC_PATH + 'stops.txt')
routes_df = pd.read_csv(GTFS_STATIC_PATH + 'routes.txt')
trips_df = pd.read_csv(GTFS_STATIC_PATH + 'trips.txt')
stop_times_df = pd.read_csv(GTFS_STATIC_PATH + 'stop_times.txt')

#Display DataFrames to ensure they are loaded correctly
st.subheader("Stops Data")
st.dataframe(stops_df.head())
    
st.subheader("Routes Data")
st.dataframe(routes_df.head())

st.subheader("Trips Data")
st.dataframe(trips_df.head())

st.subheader("Stop Times Data")
st.dataframe(stop_times_df.head())