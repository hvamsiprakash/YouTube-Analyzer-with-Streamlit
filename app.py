# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob
from PIL import Image

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to get channel analytics
def get_channel_analytics(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        channel_info = response.get("items", [])[0]["snippet"]
        statistics_info = response.get("items", [])[0]["statistics"]

        channel_title = channel_info.get("title", "N/A")
        description = channel_info.get("description", "N/A")
        published_at = channel_info.get("publishedAt", "N/A")
        country = channel_info.get("country", "N/A")

        total_videos = int(statistics_info.get("videoCount", 0))
        total_views = int(statistics_info.get("viewCount", 0))
        total_likes = int(statistics_info.get("likeCount", 0))
        total_comments = int(statistics_info.get("commentCount", 0))

        return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel analytics: {e}")
        return None

# Function to get video recommendations based on user's topic
def get_video_recommendations(topic, max_results=5):
    try:
        response = youtube.search().list(
            q=topic,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            order="relevance"
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            views = item["snippet"]["viewCount"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            likes = int(statistics_info.get("likeCount", 0))

            video_details.append((title, views, likes, url))

        return video_details
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video recommendations: {e}")
        return None

# Function to get video comments
def get_video_comments(video_id):
    try:
        comments = []
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        while "items" in results:
            for item in results["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=100,
                    pageToken=results["nextPageToken"]
                ).execute()
            else:
                break

        return comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching comments: {e}")
        return None

# Function to analyze and categorize comments
def analyze_and_categorize_comments(comments):
    categorized_comments = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity

        if polarity > 0:
            categorized_comments['Positive'] += 1
        elif polarity < 0:
            categorized_comments['Negative'] += 1
        else:
            categorized_comments['Neutral'] += 1

    return categorized_comments

# Function to generate word cloud
def generate_word_cloud(comments):
    # Generating Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(comments))

    return wordcloud

# Streamlit web app
st.set_page_config(
    page_title="YouTube Analyzer",
    page_icon="📺",
    layout="wide"
)

# Set up the layout
st.title("YouTube Analyzer")

# Sidebar for user input
st.sidebar.header("Select Task")

# Task 1: Channel Analytics with Thumbnails and Advanced Charts
if st.sidebar.button("Channel Analytics"):
    st.sidebar.subheader("Channel Analytics")
    channel_id_analytics = st.sidebar.text_input("Enter Channel ID", value="YOUR_CHANNEL_ID")

    if st.sidebar.button("Fetch Channel Analytics"):
        channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments = get_channel_analytics(channel_id_analytics)

        # Display Channel Overview
        st.subheader("Channel Overview")
        st.write(f"**Channel Title:** {channel_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Published At:** {published_at}")
        st.write(f"**Country:** {country}")
        st.write(f"**Total Videos:** {total_videos}")
        st.write(f"**Total Views:** {total_views}")
        st.write(f"**Total Likes:** {total_likes}")
        st.write(f"**Total Comments:** {total_comments}")

# Task 2: Video Recommendation based on User's Topic of Interest
if st.sidebar.button("Video Recommendation"):
    st.sidebar.subheader("Video Recommendation")
    topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="Python Tutorial")

    if st.sidebar.button("Get Video Recommendations"):
        video_recommendations = get_video_recommendations(topic_interest, max_results=5)

        # Display Video Recommendations
        st.subheader("Video Recommendations")
        for video in video_recommendations:
            st.write(f"**Title:** {video[0]}")
            st.write(f"**Views:** {video[1]}, **Likes:** {video[2]}, **URL:** {video[3]}")
            thumbnail_url = f"https://img.youtube.com/vi/{video[3].split('=')[1]}/default.jpg"
            st.image(thumbnail_url, caption=f"Video URL: {video[3]}", use_container_width=True)
            st.write("---")

# Task 3: Sentimental Analysis of Comments with Visualization and Word Cloud
if st.sidebar.button("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Analyze Sentiments and Generate Word Cloud"):
        comments_sentiment = get_video_comments(video_id_sentiment)

        # Generate Word Cloud
        wordcloud = generate_word_cloud(comments_sentiment)
        st.subheader("Word Cloud")
        st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)

        # Analyze and Categorize Comments
        categorized_comments = analyze_and_categorize_comments(comments_sentiment)

        # Display Sentimental Analysis Results
        st.subheader("Sentimental Analysis Results")
        for sentiment, count in categorized_comments.items():
            st.write(f"**{sentiment} Sentiments:** {count}")

# Footer
st.title("Connect with Me")
st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)
