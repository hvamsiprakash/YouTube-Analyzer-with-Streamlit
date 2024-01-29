# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob
from PIL import Image

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDuuUZbI7ToC7iuweYJ1MiNXAS83Goj_Cc"

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
    try:
        # Generating Word Cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(comments))

        return wordcloud
    except Exception as e:
        st.error(f"Error generating word cloud: {e}")
        return None

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

        # Advanced Charts for Channel Analytics
        st.subheader("Advanced Analytics Charts")

        # Time Series Chart for Views
        fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
        fig_views.update_layout(height=400, width=800)
        st.plotly_chart(fig_views)

        # Bar Chart for Likes and Comments
        fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
                                    title="Bar Chart for Likes and Comments", barmode="group")
        fig_likes_comments.update_layout(height=400, width=800)
        st.plotly_chart(fig_likes_comments)

        # Additional: Display DataFrame of video details with clickable URLs
        st.subheader("All Video Details")
        videos_df['URL'] = videos_df.apply(lambda row: f'<a href="{row["URL"]}" target="_blank">{row["Title"]}</a>', axis=1)
        st.write(videos_df, unsafe_allow_html=True)

# Task 2: Sentimental Analysis with Word Cloud
elif st.sidebar.button("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID for Sentimental Analysis", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Fetch Sentimental Analysis"):
        comments_sentiment = get_video_comments(video_id_sentiment)

        # Display Word Cloud for Sentimental Analysis
        st.subheader("Sentimental Analysis Word Cloud")
        if comments_sentiment:
            wordcloud = generate_word_cloud(comments_sentiment)
            st.image(wordcloud.to_array(), use_container_width=True)

        # Display Polarity Distribution
        st.subheader("Polarity Distribution")
        categorized_comments = analyze_and_categorize_comments(comments_sentiment)
        fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
                                title="Polarity Distribution", text=list(categorized_comments.values()))
        fig_polarity.update_traces(textposition="outside")
        fig_polarity.update_layout(height=400, width=800)
        st.plotly_chart(fig_polarity)

# Task 3: Video Recommendations
elif st.sidebar.button("Video Recommendations"):
    st.sidebar.subheader("Video Recommendations")
    topic_interest = st.sidebar.text_input("Enter Your Topic of Interest", "Python programming")

    if st.sidebar.button("Fetch Video Recommendations"):
        video_recommendations = get_video_recommendations(topic_interest, max_results=5)

        # Display Video Recommendations
        st.subheader("Video Recommendations")
        for video in video_recommendations:
            st.image(thumbnail_url, caption=f"Video URL: {video[3]}", use_container_width=True)


# Display the Streamlit web app
st.title("YouTube Analyzer")
st.text("Welcome to YouTube Analyzer! This tool provides insights into YouTube channels, video recommendations, and sentiment analysis of video comments. Explore the sidebar to perform different tasks.")

# Your existing code for UI elements, additional charts, or any other features goes here.

# Run the app
if __name__ == "__main__":
    st.run_app()


# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/hvamsi/) | "
    "[GitHub](https://github.com/hvamsiprakash)"
)


# Run the Streamlit app
if __name__ == '__main__':
    main()


