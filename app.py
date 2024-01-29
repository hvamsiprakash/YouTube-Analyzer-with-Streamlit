# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob

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

        # Fetch all video details for the dataframe
        videos_df = get_all_video_details(channel_id)

        return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel analytics: {e}")
        return None, None, None, None, None, None, None, None, None

# Function to fetch all video details for a channel
def get_all_video_details(channel_id):
    try:
        response = youtube.search().list(
            channelId=channel_id,
            type="video",
            part="id,snippet",
            maxResults=50
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            views = int(statistics_info.get("viewCount", 0))
            likes = int(statistics_info.get("likeCount", 0))
            comments = int(statistics_info.get("commentCount", 0))

            video_details.append((title, views, likes, comments, url))

        videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
        return videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video details: {e}")
        return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# Function to get video recommendations based on user's topic
def get_video_recommendations(topic, max_results=10):
    try:
        response = youtube.search().list(
            q=topic,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            order="viewCount"
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            views = item["snippet"]["viewCount"]
            likes = 0
            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()
            if "items" in video_info:
                statistics_info = video_info["items"][0]["statistics"]
                likes = int(statistics_info.get("likeCount", 0))

            url = f"https://www.youtube.com/watch?v={video_id}"

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

            # Get the next set of results
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    pageToken=results["nextPageToken"],
                    maxResults=100
                ).execute()
            else:
                break

        return comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching comments: {e}")
        return []

# Function to perform sentiment analysis on comments
def analyze_sentiment(comments):
    polarities = []
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
        polarities.append(polarity)

    return polarities

# Function to categorize comments based on sentiment
def categorize_comments(comments, threshold=0.1):
    categorized_comments = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for polarity in comments:
        if polarity > threshold:
            categorized_comments["Positive"] += 1
        elif polarity < -threshold:
            categorized_comments["Negative"] += 1
        else:
            categorized_comments["Neutral"] += 1

    return categorized_comments

# Function to generate a word cloud from comments
def generate_word_cloud(comments):
    try:
        text = " ".join(comments)
        wordcloud = WordCloud(width=800, height=400, random_state=21, max_font_size=110, background_color='white').generate(text)
        return wordcloud
    except Exception as e:
        st.error(f"Error generating word cloud: {e}")
        return None

# Streamlit App
def main():
    st.set_page_config(page_title="YouTube Analyzer", page_icon=":movie_camera:", layout="wide")
    st.title("YouTube Analyzer")

    # Sidebar
    st.sidebar.header("User Input")

    # Get user input for channel ID
    channel_id = st.sidebar.text_input("Enter YouTube Channel ID:", "UC4JX40jDee_tINbkjycV4Sg")

    # Fetch channel analytics
    channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(
        channel_id)

    # Display channel analytics
    if channel_title is not None:
        st.header(f"Channel Analytics: {channel_title}")
        st.subheader("Description")
        st.write(description)
        st.subheader("Published At")
        st.write(published_at)
        st.subheader("Country")
        st.write(country)
        st.subheader("Total Videos")
        st.write(total_videos)
        st.subheader("Total Views")
        st.write(total_views)
        st.subheader("Total Likes")
        st.write(total_likes)
        st.subheader("Total Comments")
        st.write(total_comments)

    # Display all video details
    st.sidebar.header("All Video Details")

    # Error handling for displaying video details
    try:
        st.sidebar.dataframe(videos_df.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False),
                             unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying video details: {e}")

    # Sidebar for video recommendations
    st.sidebar.header("Video Recommendations")

    # Get user input for topic of interest
    topic_interest = st.sidebar.text_input("Enter Topic of Interest:", "Python Programming")

    # Fetch video recommendations
    video_recommendations = get_video_recommendations(topic_interest, max_results=10)

    # Display video recommendations
    if video_recommendations:
        st.header("Video Recommendations")
        recommendation_data = pd.DataFrame(video_recommendations,
                                          columns=["Title", "Views", "Likes", "URL"])
        st.dataframe(recommendation_data.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False),
                     unsafe_allow_html=True)

    # Sentiment Analysis
    st.sidebar.header("Sentiment Analysis")

    # Fetch comments for sentiment analysis
    comments_sentiment = get_video_comments("EXAMPLE_VIDEO_ID")

    # Perform sentiment analysis
    polarities = analyze_sentiment(comments_sentiment)

    # Categorize comments based on sentiment
    categorized_comments = categorize_comments(polarities)

    # Display sentiment analysis results
    st.header("Sentiment Analysis Visualization")

    # Bar Chart for Sentiment Analysis
    fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
                          labels={'x': 'Sentiment', 'y': 'Count'}, title="Sentiment Analysis of Comments")
    st.plotly_chart(fig_polarity)

    # Generate Word Cloud
    wordcloud = generate_word_cloud(comments_sentiment)
    if wordcloud is not None:
        st.subheader("Word Cloud for Comments")
        st.image(wordcloud.to_image(), use_container_width=True)

if __name__ == "__main__":
    main()
