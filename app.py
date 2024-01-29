# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import plotly.express as px
import pandas as pd
from wordcloud import WordCloud
from PIL import Image
import requests
import random

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to get channel details
def get_channel_details(channel_id):
    try:
        channel_info = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        snippet_info = channel_info.get("items", [])[0]["snippet"]
        statistics_info = channel_info.get("items", [])[0]["statistics"]

        channel_title = snippet_info.get("title", "N/A")
        description = snippet_info.get("description", "N/A")
        published_at = snippet_info.get("publishedAt", "N/A")
        country = snippet_info.get("country", "N/A")
        total_videos = int(statistics_info.get("videoCount", 0))
        total_views = int(statistics_info.get("viewCount", 0))
        total_likes = int(statistics_info.get("likeCount", 0))
        total_comments = int(statistics_info.get("commentCount", 0))

        return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel details: {e}")
        return "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0

# Function to get channel videos
def get_channel_videos(channel_id, max_results=5):
    try:
        response = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=max_results,
            order="date"
        ).execute()

        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        return video_ids
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel videos: {e}")
        return []

# Function to generate word cloud
def generate_word_cloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(text))
    return wordcloud

# Function to generate thumbnail grid
def generate_thumbnail_grid(video_ids):
    thumbnail_grid = Image.new("RGB", (800, 400))
    x_offset = 0
    y_offset = 0
    thumbnail_size = (100, 100)

    for video_id in video_ids:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
        thumbnail_image = Image.open(requests.get(thumbnail_url, stream=True).raw)
        thumbnail_image = thumbnail_image.resize(thumbnail_size)
        thumbnail_grid.paste(thumbnail_image, (x_offset, y_offset))

        x_offset += thumbnail_size[0]
        if x_offset + thumbnail_size[0] > thumbnail_grid.width:
            x_offset = 0
            y_offset += thumbnail_size[1]

    return thumbnail_grid

# Function to get video details
def get_video_details(video_id):
    try:
        video_info = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()

        snippet_info = video_info.get("items", [])[0]["snippet"]
        statistics_info = video_info.get("items", [])[0]["statistics"]

        video_title = snippet_info.get("title", "N/A")
        video_views = int(statistics_info.get("viewCount", 0))
        video_likes = int(statistics_info.get("likeCount", 0))
        video_comments = int(statistics_info.get("commentCount", 0))

        return video_title, video_views, video_likes, video_comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video details: {e}")
        return "N/A", 0, 0, 0

# Streamlit web app
st.set_page_config(
    page_title="YouTube Channel Analytics",
    page_icon="📊",
    layout="wide"
)

# Set up the layout
st.title("YouTube Channel Analytics")
st.info(
    "Explore various analytics about a YouTube channel. Choose a task from the sidebar to get insights."
)

# Sidebar for user input
st.sidebar.header("Choose a Task")

# Task 1: Channel Overview
if st.sidebar.button("Channel Overview"):
    st.sidebar.subheader("Channel Overview")
    channel_id_overview = st.sidebar.text_input("Enter Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")

    if st.sidebar.button("Fetch Channel Overview"):
        channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments = get_channel_details(channel_id_overview)

        st.subheader("Channel Overview")
        st.write(f"**Channel Title:** {channel_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Published At:** {published_at}")
        st.write(f"**Country:** {country}")
        st.write(f"**Total Videos:** {total_videos}")
        st.write(f"**Total Views:** {total_views}")
        st.write(f"**Total Likes:** {total_likes}")
        st.write(f"**Total Comments:** {total_comments}")

        # Visualization 1: Bar chart for Total Videos, Views, Likes, and Comments
        overview_data = {
            "Metric": ["Total Videos", "Total Views", "Total Likes", "Total Comments"],
            "Count": [total_videos, total_views, total_likes, total_comments]
        }
        overview_df = pd.DataFrame(overview_data)
        fig_overview = px.bar(overview_df, x="Metric", y="Count", title="Channel Overview Metrics")
        st.plotly_chart(fig_overview, use_container_width=True)

# Task 2: Latest Channel Videos
elif st.sidebar.button("Latest Channel Videos"):
    st.sidebar.subheader("Latest Channel Videos")
    channel_id_latest = st.sidebar.text_input("Enter Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")

    if st.sidebar.button("Fetch Latest Channel Videos"):
        video_ids_latest = get_channel_videos(channel_id_latest)
        video_data_latest = []

        for video_id_latest in video_ids_latest:
            video_title_latest, video_views_latest, video_likes_latest, video_comments_latest = get_video_details(video_id_latest)

            video_data_latest.append({
                "Video ID": video_id_latest,
                "Title": video_title_latest,
                "Views": video_views_latest,
                "Likes": video_likes_latest,
                "Comments": video_comments_latest
            })

        video_df_latest = pd.DataFrame(video_data_latest)

        # Visualizations for Latest Channel Videos
        if st.sidebar.checkbox("Show Visualizations for Latest Channel Videos"):
            st.sidebar.subheader("Visualizations for Latest Channel Videos")

            # Visualization 1: Bar chart for Views, Likes, and Comments
            fig_views_latest = px.bar(video_df_latest, x="Video ID", y=["Views", "Likes", "Comments"],
                                       title="Engagement Metrics for Latest Channel Videos")
            st.plotly_chart(fig_views_latest, use_container_width=True)

            # Visualization 2: Time series line chart for Views
            video_df_latest["Published At"] = pd.to_datetime(video_df_latest["Published At"])
            fig_time_series_latest = px.line(video_df_latest, x="Published At", y="Views", title="Time Series of Views for Latest Videos")
            st.plotly_chart(fig_time_series_latest, use_container_width=True)

# Task 3: Word Cloud and Thumbnails for Latest Channel Videos
elif st.sidebar.button("Word Cloud and Thumbnails"):
    st.sidebar.subheader("Word Cloud and Thumbnails")
    channel_id_wordcloud = st.sidebar.text_input("Enter Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")

    if st.sidebar.button("Generate Word Cloud and Thumbnails"):
        video_ids_wordcloud = get_channel_videos(channel_id_wordcloud)
        comments_wordcloud = []

        for video_id_wordcloud in video_ids_wordcloud:
            comments_wordcloud.extend(get_video_comments(video_id_wordcloud))

        # Generate Word Cloud
        wordcloud = generate_word_cloud(comments_wordcloud)
        st.subheader("Word Cloud")
        st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)

        # Generate Thumbnail Grid
        thumbnail_grid_image = generate_thumbnail_grid(video_ids_wordcloud)
        st.subheader("Thumbnail Grid for Latest Channel Videos")
        st.image(thumbnail_grid_image, caption="Thumbnail Grid", use_container_width=True)

# ... (Other tasks and code)

# Footer
st.title("Connect with Me")
st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)
