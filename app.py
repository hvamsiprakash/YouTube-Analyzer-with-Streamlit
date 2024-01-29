# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob

# Set your YouTube Data API key here
YOUTUBE_API_KEY =  "AIzaSyDuuUZbI7ToC7iuweYJ1MiNXAS83Goj_Cc"

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
            order="viewCount"  # Order by views to get top-viewed videos
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
            comments = int(statistics_info.get("commentCount", 0))

            video_details.append((title, views, likes, comments, url))

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
        st.error(f"Error fetching video comments: {e}")
        return None

# Function to categorize and analyze sentiment of comments
def analyze_sentiment(comments):
    positive_comments = 0
    neutral_comments = 0
    negative_comments = 0

    for comment in comments:
        analysis = TextBlob(comment)

        # Classify the polarity of the comment
        if analysis.sentiment.polarity > 0:
            positive_comments += 1
        elif analysis.sentiment.polarity == 0:
            neutral_comments += 1
        else:
            negative_comments += 1

    return positive_comments, neutral_comments, negative_comments

# Function to generate a word cloud from comments
def generate_word_cloud(comments):
    try:
        # Combine all comments into a single string
        all_comments = " ".join(comments)

        # Generate the word cloud
        wordcloud = WordCloud(width=800, height=400, random_state=21, max_font_size=110, background_color='white').generate(all_comments)

        return wordcloud
    except Exception as e:
        st.error(f"Error generating word cloud: {e}")
        return None

# Set page configuration
st.set_page_config(page_title="YouTube Analyzer", page_icon=":movie_camera:", layout="wide")

# Display the header
st.title("YouTube Analyzer")

# User input for the channel ID
channel_id = st.text_input("Enter YouTube Channel ID:", "UC4JX40jDee_tINbkjycV4Sg")

# Fetch channel analytics
channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id)

# Display channel analytics
if channel_title:
    st.subheader("Channel Analytics")
    st.write(f"**Channel Title:** {channel_title}")
    st.write(f"**Description:** {description}")
    st.write(f"**Published At:** {published_at}")
    st.write(f"**Country:** {country}")
    st.write(f"**Total Videos:** {total_videos}")
    st.write(f"**Total Views:** {total_views}")
    st.write(f"**Total Likes:** {total_likes}")
    st.write(f"**Total Comments:** {total_comments}")

    # Display all video details
    st.subheader("All Video Details")
    st.dataframe(videos_df.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False), unsafe_allow_html=True)

    # Get user input for video recommendations
    st.subheader("Video Recommendations")
    topic_interest = st.text_input("Enter your topic of interest:", "Python programming")

    # Fetch video recommendations
    video_recommendations = get_video_recommendations(topic_interest, max_results=10)

    # Display video recommendations
    if video_recommendations:
        st.write("**Top Video Recommendations:**")
        for i, video in enumerate(video_recommendations, start=1):
            st.write(f"{i}. **Title:** {video[0]}")
            st.write(f"   **Views:** {video[1]}")
            st.write(f"   **Likes:** {video[2]}")
            st.write(f"   **Comments:** {video[3]}")
            st.write(f"   **URL:** [{video[4]}]({video[4]})")

        # Fetch comments for the first recommended video
        if video_recommendations[0]:
            st.subheader("Comments Analysis")
            st.write(f"Analyzing comments for the video: {video_recommendations[0][0]}")

            video_comments = get_video_comments(video_recommendations[0][-1].split("=")[-1])

            if video_comments:
                # Analyze sentiment of comments
                positive_comments, neutral_comments, negative_comments = analyze_sentiment(video_comments)

                # Display sentiment analysis
                st.write(f"**Sentiment Analysis:**")
                st.write(f"   Positive Comments: {positive_comments}")
                st.write(f"   Neutral Comments: {neutral_comments}")
                st.write(f"   Negative Comments: {negative_comments}")

                # Display bar chart for sentiment analysis
                fig_polarity = px.bar(x=["Positive", "Neutral", "Negative"],
                                      y=[positive_comments, neutral_comments, negative_comments],
                                      labels={'y': 'Number of Comments', 'x': 'Sentiment'},
                                      color=["Positive", "Neutral", "Negative"],
                                      title="Sentiment Analysis of Comments")
                st.plotly_chart(fig_polarity)

                # Generate Word Cloud
                wordcloud = generate_word_cloud(video_comments)
                if wordcloud is not None:
                    st.subheader("Word Cloud for Comments")
                    st.image(wordcloud.to_image(), use_container_width=True)
            else:
                st.warning("No comments available for analysis.")
else:
    st.warning("Invalid Channel ID. Please enter a valid YouTube Channel ID.")
