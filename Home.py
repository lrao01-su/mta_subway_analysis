# Home.py
import streamlit as st

# Set page config
st.set_page_config(
    page_title="NYC MTA Subway Dashboard",
    page_icon="🚇",
    layout="wide"
)

# Title and introduction
st.title("🗽 NYC MTA Subway Dashboard")

st.markdown("""
As New York City rebounds from the pandemic, this streamlit dashboard is leveraging the MTA's newly released 
subway origin-destination dataset to visualize the city's recovery. It aims to offer
a unique glimpse into how NYC is getting back on track, one subway ride at a time.

Explore ridership trends, station data, and travel patterns to see how the pulse of the 
city is changing. 

Please use the sidebar to navigate through the insights!


### 🔍 Insight Sections:

1. 📊 **Ridership Trends**: Analyze passenger flow patterns over time.
2. 🗺️ **Station Map**: Visualize the subway network and station information.
3. 📈 **Origin-Destination Ridership*: View the origin-destination ridership data, understanding the flow of the people.

### 🚀 Get Started:
Use the sidebar to navigate through different sections of the dashboard. Each page offers 
unique insights into the NYC subway system.

### 📚 About the Data:
This dashboard uses official MTA data to provide analysis on the subway system. The data sources include:
            
[Accessible Station Platform Availability](https://data.ny.gov/Transportation/MTA-Subway-Accessible-Station-Platform-Availabilit/thh2-syn7/about_data)
            
[Daily Ridership Data Beginning 2020](https://data.ny.gov/Transportation/MTA-Daily-Ridership-Data-Beginning-2020/vxuj-8kew/about_data)
            
[MTA Subway Station](https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f/about_data)
            
[GTFS Real time / Static Feed](https://new.mta.info/developers)
            
[Subway Origin Destionation Ridership Estimate](https://data.ny.gov/Transportation/MTA-Subway-Origin-Destination-Ridership-Estimate-2/jsu2-fbtj/about_data)

### 🎯 Goal:
The aim is to dive in and discover the pulse of New York City's subway system!
Were are the busiest stations? What are the peak hours? How has ridership changed over time?
Which stations are the most accessible? Let's find out!
""")

# some key statistics and a subway meme for fun
st.subheader("📌 Quick Stats")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Stations", value="472")
with col2:
    st.metric(label="Daily Ridership (Avg. 2023)", value="3.4M")
with col3:
    st.metric(label="Subway lines", value="36")
with col4:
    st.image("data/NYC_subway.png", use_column_width=True)

# Add a note about data sources
st.info("""
💡 **Data Source**: All data is sourced from the Metropolitan Transportation Authority (MTA). 
For more information, check out the [MTA website](http://web.mta.info/developers/).
""")

# Optional: Add a footer
st.markdown("""
---
Created with ❤️ using Streamlit by Linjing maryljrao.com
""")