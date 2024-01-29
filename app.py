# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from textblob import TextBlob

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

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
def get_video_recommendations(channel_id, max_results=10):
    try:
        response = youtube.search().list(
            channelId=channel_id,
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

        videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
        return videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video recommendations: {e}")
        return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# Function to analyze and categorize comments sentiment
def analyze_and_categorize_comments(comments):
    categorized_comments = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for comment in comments:
        analysis = TextBlob(comment).sentiment.polarity
        if analysis > 0:
            categorized_comments["Positive"] += 1
        elif analysis < 0:
            categorized_comments["Negative"] += 1
        else:
            categorized_comments["Neutral"] += 1
    return categorized_comments

# Function to generate word cloud
def generate_word_cloud(comments):
    try:
        comments_text = " ".join(comments)
        wordcloud = WordCloud(width=800, height=400, random_state=21, max_font_size=110).generate(comments_text)
        return wordcloud
    except Exception as e:
        st.error(f"Error generating word cloud: {e}")
        return None

# Main function to run the Streamlit app
def main():
    # Set Streamlit page configuration
    st.set_page_config(page_title="YouTube Analyzer", page_icon=":movie_camera:", layout="wide")

    # Sidebar for user input
    st.sidebar.title("YouTube Analyzer")
    st.sidebar.subheader("Enter YouTube Channel ID:")
    channel_id = st.sidebar.text_input("Channel ID", "UC4JX40jDee_tINbkjycV4Sg")

    if st.sidebar.button("Analyze"):
        # Channel Analytics Section
        st.title("Channel Analytics")
        channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id)

        if channel_title is not None:
            st.write(f"**Channel Title:** {channel_title}")
            st.write(f"**Description:** {description}")
            st.write(f"**Published At:** {published_at}")
            st.write(f"**Country:** {country}")
            st.write(f"**Total Videos:** {total_videos}")
            st.write(f"**Total Views:** {total_views}")
            st.write(f"**Total Likes:** {total_likes}")
            st.write(f"**Total Comments:** {total_comments}")

            # All Video Details Section
            st.title("All Video Details")
            if not videos_df.empty:
                st.dataframe(videos_df)
            else:
                st.warning("No video details available.")

            # Video Recommendations Section
            st.title("Video Recommendations")
            video_recommendations = get_video_recommendations(channel_id, max_results=10)
            if not video_recommendations.empty:
                st.dataframe(video_recommendations)
            else:
                st.warning("No video recommendations available.")

            # Sentiment Analysis Section
            st.title("Sentiment Analysis of Comments with Visualization and Word Cloud")

            # Fetch all video comments
            comments = []
            for video_url in videos_df["URL"]:
                video_id = video_url.split("=")[-1]
                video_comments = get_video_comments(video_id)
                comments.extend(video_comments)

            # Sentiment Analysis Visualization
            st.subheader("Sentiment Analysis Visualization")

            # Bar Chart for Sentiment Analysis
            categorized_comments = analyze_and_categorize_comments(comments)
            fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
                                  title="Sentiment Analysis Bar Chart", labels={'x': 'Sentiment', 'y': 'Count'})
            fig_polarity.update_layout(height=400, width=800)
            st.plotly_chart(fig_polarity)

            # Generate Word Cloud
            wordcloud = generate_word_cloud(comments)
            if wordcloud is not None:
                st.subheader("Word Cloud for Comments")
                st.image(wordcloud.to_image(), use_container_width=True)

# Run the app
if __name__ == "__main__":
    main()
