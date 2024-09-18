import pandas as pd
import streamlit as st
import plotly.graph_objects as go

@st.cache
def load_ridership_data():
    # Load the MTA ridership data from a CSV file
    file_path = "data/MTA_Daily_Ridership_Data__Beginning_2020_20240911.csv"
    df = pd.read_csv(file_path, parse_dates=['Date'])
    
    # Rename columns for easier access and readability
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
    
    # Add a new column to indicate whether a date is a weekday or weekend
    df['Day of Week'] = df['Date'].dt.day_name()
    df['Is Weekend'] = df['Day of Week'].isin(['Saturday', 'Sunday'])
    
    # Aggregate data to monthly for the main chart
    df['Month'] = df['Date'].dt.to_period('M')
    
    # Filter for numeric columns only
    numeric_columns = df.select_dtypes(include=['number']).columns

    # Group by 'Month' and calculate the mean for numeric columns
    monthly_df = df.groupby('Month')[numeric_columns].mean().reset_index()
    
    # Convert 'Month' back to a timestamp
    monthly_df['Month'] = monthly_df['Month'].dt.to_timestamp()
    
    return df, monthly_df


def create_interactive_chart(df, selected_types, show_pandemic_percentage):
    # Create an interactive line chart using Plotly
    fig = go.Figure()

    # Add a line plot for each selected transportation type
    for column in selected_types:
        fig.add_trace(go.Scatter(
            x=df['Month'],
            y=df[column],
            mode='lines+markers',
            name=column
        ))

    # Set chart title and y-axis labels based on user options
    title_suffix = "Monthly Average Ridership"
    y_axis_title = "Average Monthly Ridership"
    
    if show_pandemic_percentage:
        title_suffix = "Monthly Average % of Pre-Pandemic Ridership"
        y_axis_title = "Average % of Pre-Pandemic"

    # Update layout for the chart
    fig.update_layout(
        title=f'MTA {title_suffix}',
        xaxis_title='Month',
        yaxis_title=y_axis_title,
        legend_title='Transportation Types',
        hovermode='x unified'
    )

    return fig

def plot_weekday_vs_weekend(df, selected_column):
    # Create a new DataFrame to compare ridership on weekdays vs weekends
    weekend_vs_weekday = df.groupby(['Is Weekend'])[[selected_column]].mean().reset_index()

    # Create a bar chart comparing weekdays and weekends
    fig = go.Figure(
        data=[
            go.Bar(name="Weekdays", x=['Weekdays'], y=weekend_vs_weekday.loc[weekend_vs_weekday['Is Weekend'] == False, selected_column]),
            go.Bar(name="Weekends", x=['Weekends'], y=weekend_vs_weekday.loc[weekend_vs_weekday['Is Weekend'] == True, selected_column])
        ]
    )

    # Customize the layout of the bar chart
    fig.update_layout(
        title=f'Weekday vs Weekend {selected_column} Ridership',
        xaxis_title='Type of Day',
        yaxis_title=f'Average {selected_column} Ridership',
        barmode='group'
    )
    
    return fig

# Streamlit app
st.set_page_config(page_title="MTA Ridership Trends", page_icon="📊", layout="wide")

st.title('📊 MTA Ridership Trends')

# Load the ridership data (returns both daily and monthly aggregated data)
daily_ridership_df, ridership_df = load_ridership_data()


# Sidebar for user controls
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

# Main content - Plot the ridership chart
if selected_types:
    if data_view == "Pandemic Percentage Data":
        selected_columns = [col.replace("Ridership", "% of Pre-Pandemic").replace("Traffic", "% of Pre-Pandemic") for col in selected_types]
    else:
        selected_columns = selected_types
    
    updated_chart = create_interactive_chart(filtered_df, selected_columns, data_view == "Pandemic Percentage Data")
    st.plotly_chart(updated_chart, use_container_width=True)
else:
    st.warning("Please select at least one transportation type.")


# Display raw data option
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
