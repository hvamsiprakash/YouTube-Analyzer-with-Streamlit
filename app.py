import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to fetch channel analytics data
def get_channel_analytics(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        ).execute()

        channel_info = response.get("items", [])[0]
        statistics = channel_info["statistics"]

        return {
            "Subscribers": int(statistics.get("subscriberCount", 0)),
            "Views": int(statistics.get("viewCount", 0)),
            "Videos": int(statistics.get("videoCount", 0)),
        }

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel analytics: {e}")
        return {}

# Function to fetch daily views time series
def get_daily_views_time_series(channel_id):
    try:
        response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()

        uploads_playlist_id = response.get("items", [])[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50  # Fetch the latest 50 videos
        ).execute()

        video_ids = [item["contentDetails"]["videoId"] for item in response.get("items", [])]
        video_ids_str = ",".join(video_ids)

        response = youtube.videos().list(
            part="statistics,snippet",
            id=video_ids_str
        ).execute()

        video_data = [(item["snippet"]["publishedAt"], int(item["statistics"]["viewCount"])) for item in response.get("items", [])]

        df = pd.DataFrame(video_data, columns=["PublishedAt", "Views"])
        df["PublishedAt"] = pd.to_datetime(df["PublishedAt"])
        df.set_index("PublishedAt", inplace=True)
        df.sort_index(inplace=True)

        daily_views = df.resample('D').sum()
        daily_views.reset_index(inplace=True)

        return daily_views

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching daily views time series: {e}")
        return pd.DataFrame()

# Streamlit web app
st.set_page_config(
    page_title="Advanced Channel Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Set up the layout
st.title("Advanced Channel Analytics Dashboard")
st.info(
    "This advanced dashboard displays analytics for a YouTube channel. "
    "Enter the channel ID in the sidebar to view advanced analytics."
)

# Sidebar for user input
st.sidebar.header("Enter Channel ID")
channel_id = st.sidebar.text_input("Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")

if st.sidebar.button("Fetch Analytics"):
    analytics_data = get_channel_analytics(channel_id)

    if analytics_data:
        # Display basic analytics data
        st.subheader("Basic Channel Analytics")
        st.write(analytics_data)

        # Fetch and display daily views time series
        daily_views_data = get_daily_views_time_series(channel_id)

        if not daily_views_data.empty:
            st.subheader("Daily Views Time Series")
            st.line_chart(daily_views_data.set_index("PublishedAt"))

            # Plot cumulative views over time
            st.subheader("Cumulative Views Over Time")
            fig_cumulative = go.Figure()
            fig_cumulative.add_trace(go.Scatter(x=daily_views_data["PublishedAt"], y=daily_views_data["Views"].cumsum(), mode='lines+markers', name='Cumulative Views'))
            fig_cumulative.update_layout(title='Cumulative Views Over Time', xaxis_title='Date', yaxis_title='Cumulative Views')
            st.plotly_chart(fig_cumulative)

# Credits
st.title("Credits")
st.info(
    "This Streamlit app was created by [Your Name]."
)

# Footer
st.title("Connect with Me")
st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)

