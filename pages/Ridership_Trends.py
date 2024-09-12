import pandas as pd
import streamlit as st
import plotly.graph_objects as go

@st.cache
def load_ridership_data():
    file_path = "data/MTA_Daily_Ridership_Data__Beginning_2020_20240911.csv"
    df = pd.read_csv(file_path, parse_dates=['Date'])
    
    # Rename columns
    column_mapping = {
        'Subways: Total Estimated Ridership': 'Subway Ridership',
        'Buses: Total Estimated Ridership': 'Bus Ridership',
        'LIRR: Total Estimated Ridership': 'LIRR Ridership',
        'Metro-North: Total Estimated Ridership': 'Metro-North Ridership',
        'Access-A-Ride: Total Scheduled Trips': 'Access-A-Ride Ridership',
        'Bridges and Tunnels: Total Traffic': 'Bridges and Tunnels Traffic',
        'Staten Island Railway: Total Estimated Ridership': 'Staten Island Railway Ridership',
        'Subways: % of Comparable Pre-Pandemic Day': 'Subway % of Pre-Pandemic',
        'Buses: % of Comparable Pre-Pandemic Day': 'Bus % of Pre-Pandemic',
        'LIRR: % of Comparable Pre-Pandemic Day': 'LIRR % of Pre-Pandemic',
        'Metro-North: % of Comparable Pre-Pandemic Day': 'Metro-North % of Pre-Pandemic',
        'Access-A-Ride: % of Comparable Pre-Pandemic Day': 'Access-A-Ride % of Pre-Pandemic',
        'Bridges and Tunnels: % of Comparable Pre-Pandemic Day': 'Bridges and Tunnels % of Pre-Pandemic',
        'Staten Island Railway: % of Comparable Pre-Pandemic Day': 'Staten Island Railway % of Pre-Pandemic'
    }
    df = df.rename(columns=column_mapping)
    
    # Aggregate data to monthly
    df['Month'] = df['Date'].dt.to_period('M')
    monthly_df = df.groupby('Month').mean().reset_index()
    monthly_df['Month'] = monthly_df['Month'].dt.to_timestamp()
    
    return monthly_df

def create_interactive_chart(df, selected_types, show_pandemic_percentage):
    fig = go.Figure()

    for column in selected_types:
        fig.add_trace(go.Scatter(
            x=df['Month'],
            y=df[column],
            mode='lines+markers',
            name=column
        ))

    title_suffix = "Monthly Average Ridership"
    y_axis_title = "Average Monthly Ridership"
    
    if show_pandemic_percentage:
        title_suffix = "Monthly Average % of Pre-Pandemic Ridership"
        y_axis_title = "Average % of Pre-Pandemic"

    fig.update_layout(
        title=f'MTA {title_suffix}',
        xaxis_title='Month',
        yaxis_title=y_axis_title,
        legend_title='Transportation Types',
        hovermode='x unified'
    )

    return fig

# Streamlit app
st.set_page_config(page_title="MTA Ridership Trends", page_icon="📊", layout="wide")

st.title('📊 MTA Ridership Trends')

# Load data
ridership_df = load_ridership_data()

# Sidebar for controls
st.sidebar.header("Controls")

# Year-Month range selector
min_date = ridership_df['Month'].min()
max_date = ridership_df['Month'].max()

col1, col2 = st.sidebar.columns(2)

with col1:
    start_year = st.selectbox("Start Year", options=range(min_date.year, max_date.year + 1), index=0)
    start_month = st.selectbox("Start Month", options=range(1, 13), index=0)

with col2:
    end_year = st.selectbox("End Year", options=range(min_date.year, max_date.year + 1), index=len(range(min_date.year, max_date.year + 1)) - 1)
    end_month = st.selectbox("End Month", options=range(1, 13), index=11)

start_date = pd.Timestamp(year=start_year, month=start_month, day=1)
end_date = pd.Timestamp(year=end_year, month=end_month, day=1)

# Ensure start date is not after end date
if start_date > end_date:
    st.sidebar.warning("Start date is after end date. Please adjust your selection.")
    start_date, end_date = end_date, start_date

# Transportation type selector
ridership_columns = ['Subway Ridership', 'Bus Ridership', 'LIRR Ridership', 
                     'Metro-North Ridership', 'Access-A-Ride Ridership', 
                     'Bridges and Tunnels Traffic', 'Staten Island Railway Ridership']

pandemic_columns = ['Subway % of Pre-Pandemic', 'Bus % of Pre-Pandemic', 'LIRR % of Pre-Pandemic',
                    'Metro-North % of Pre-Pandemic', 'Access-A-Ride % of Pre-Pandemic',
                    'Bridges and Tunnels % of Pre-Pandemic', 'Staten Island Railway % of Pre-Pandemic']

# Dropdown for selecting all or specific types
selection_option = st.sidebar.selectbox(
    "Select Transportation Types",
    ["All Types", "Select Specific Types"]
)

if selection_option == "All Types":
    selected_types = ridership_columns
else:
    selected_types = st.sidebar.multiselect(
        "Choose Transportation Types",
        options=ridership_columns,
        default=['Subway Ridership', 'Bus Ridership']
    )

# Radio button for choosing between ridership and pandemic percentage
data_view = st.sidebar.radio(
    "Select Data View",
    ("Ridership Data", "Pandemic Percentage Data")
)

# Filter the data based on user selection
filtered_df = ridership_df[
    (ridership_df['Month'] >= start_date) &
    (ridership_df['Month'] <= end_date)
]

# Main content
if selected_types:
    if data_view == "Pandemic Percentage Data":
        selected_columns = [col.replace("Ridership", "% of Pre-Pandemic").replace("Traffic", "% of Pre-Pandemic") for col in selected_types]
    else:
        selected_columns = selected_types
    
    updated_chart = create_interactive_chart(filtered_df, selected_columns, data_view == "Pandemic Percentage Data")
    st.plotly_chart(updated_chart, use_container_width=True)
else:
    st.warning("Please select at least one transportation type.")


# Display raw data
if st.checkbox("Show Raw Data"):
    st.subheader("Raw Data")
    st.dataframe(filtered_df)

# Add a download button for the filtered data
if st.button("Download Filtered Data as CSV"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Click here to download",
        data=csv,
        file_name="filtered_mta_ridership_data.csv",
        mime="text/csv",
    )