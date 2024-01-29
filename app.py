import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from textblob import TextBlob
from wordcloud import WordCloud
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to fetch channel details
def get_channel_details(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        ).execute()

        channel_info = response.get("items", [])[0]
        snippet_info = channel_info.get("snippet", {})
        content_details = channel_info.get("contentDetails", {})
        statistics_info = channel_info.get("statistics", {})

        channel_title = snippet_info.get("title", "N/A")
        description = snippet_info.get("description", "N/A")
        published_at = snippet_info.get("publishedAt", "N/A")
        country = snippet_info.get("country", "N/A")
        total_videos = statistics_info.get("videoCount", 0)
        total_views = statistics_info.get("viewCount", 0)
        total_likes = statistics_info.get("likeCount", 0)
        total_comments = statistics_info.get("commentCount", 0)
        total_subscribers = statistics_info.get("subscriberCount", 0)

        return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, total_subscribers

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel details: {e}")
        return "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0, 0

# Function to fetch video details for a channel
def get_channel_videos(channel_id):
    try:
        response = youtube.search().list(
            part="id",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=50
        ).execute()

        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        return video_ids

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel videos: {e}")
        return []

# Function to fetch video details
def get_video_details(video_id):
    try:
        response = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()

        video_info = response.get("items", [])[0]
        snippet_info = video_info.get("snippet", {})
        statistics_info = video_info.get("statistics", {})

        title = snippet_info.get("title", "N/A")
        views = int(statistics_info.get("viewCount", 0))
        comments = int(statistics_info.get("commentCount", 0))
        likes = int(statistics_info.get("likeCount", 0))
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        thumbnail_url = snippet_info.get("thumbnails", {}).get("medium", {}).get("url", "N/A")

        return title, views, comments, likes, video_url, thumbnail_url

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video details: {e}")
        return "N/A", 0, 0, 0, "N/A", "N/A"

# Function to fetch more detailed statistics
def get_video_statistics(video_id):
    try:
        response = youtube.videos().list(
            part="statistics",
            id=video_id
        ).execute()

        statistics_info = response.get("items", [])[0].get("statistics", {})

        return statistics_info

    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video statistics: {e}")
        return {}

# Function to fetch video comments using the video ID
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
        return []

# Placeholder function for sentiment analysis
def analyze_and_categorize_comments(comments):
    categorized_comments = {'Positive': [], 'Negative': [], 'Neutral': []}
    for comment in comments:
        analysis = TextBlob(comment)
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity

        if polarity > 0:
            categorized_comments['Positive'].append((comment, polarity, subjectivity))
        elif polarity < 0:
            categorized_comments['Negative'].append((comment, polarity, subjectivity))
        else:
            categorized_comments['Neutral'].append((comment, polarity, subjectivity))

    return categorized_comments

# Placeholder function for word cloud generation
def generate_word_cloud(comments):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(" ".join(comments))
    keywords = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]

    # Generating Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(keywords))

    # Display Word Cloud
    st.subheader("Word Cloud")
    st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)

# Streamlit web app
st.set_page_config(
    page_title="YouTube Channel Analytics",
    page_icon="📊",
    layout="wide"
)

# Set up the layout
st.title("YouTube Channel Analytics")
st.info(
    "This tool provides detailed analytics for a YouTube channel. "
    "Enter the channel ID to get started."
)

# Sidebar for user input
channel_id = st.sidebar.text_input("Enter Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")

if st.sidebar.button("Analyze Channel"):
    # Fetch channel details
    channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, total_subscribers = get_channel_details(channel_id)

    if channel_title != "N/A":
        # Display channel details
        st.subheader("Channel Details")
        st.write(f"**Title:** {channel_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Published At:** {published_at}")
        st.write(f"**Country:** {country}")
        st.write(f"**Total Videos:** {total_videos}")
        st.write(f"**Total Views:** {total_views}")
        st.write(f"**Total Likes:** {total_likes}")
        st.write(f"**Total Comments:** {total_comments}")
        st.write(f"**Total Subscribers:** {total_subscribers}")

        # Additional visualizations
        st.subheader("Channel Performance Over Time")
        st.write("Note: This analysis includes the 50 most recent videos.")
        
        # Fetch video details for the channel
        video_ids = get_channel_videos(channel_id)
        video_data = []
        for video_id in video_ids:
            title, views, comments, likes, video_url, thumbnail_url = get_video_details(video_id)
            video_data.append({
                "Title": title,
                "Views": views,
                "Comments": comments,
                "Likes": likes,
                "Video URL": video_url,
                "Thumbnail URL": thumbnail_url
            })

        video_df = pd.DataFrame(video_data)

        # Display video details
        st.subheader("Recent Video Details")
        st.dataframe(video_df)

        # Visualize video details (e.g., views, likes, comments)
        fig_views = px.bar(video_df, x="Title", y="Views", title="Views of Recent Videos")
        fig_likes = px.bar(video_df, x="Title", y="Likes", title="Likes of Recent Videos")
        fig_comments = px.bar(video_df, x="Title", y="Comments", title="Comments on Recent Videos")

        st.plotly_chart(fig_views, use_container_width=True)
        st.plotly_chart(fig_likes, use_container_width=True)
        st.plotly_chart(fig_comments, use_container_width=True)

        # Fetch and analyze video comments
        all_comments = []
        for video_id in video_ids:
            comments = get_video_comments(video_id)
            all_comments.extend(comments)

        if all_comments:
            # Analyze sentiment of comments
            categorized_sentiments = analyze_and_categorize_comments(all_comments)

            # Display sentiment analysis results
            st.subheader("Sentiment Analysis Results")
            for sentiment, comments in categorized_sentiments.items():
                st.write(f"**{sentiment} Sentiments:**")
                for comment in comments:
                    st.write(comment[0])
                st.write("---")

            # Generate Word Cloud
            generate_word_cloud(all_comments)
        else:
            st.warning("No comments available for sentiment analysis.")
    else:
        st.warning("Channel details not available.")

# Footer
st.title("About")
st.info(
    "This YouTube Channel Analytics tool was created by [Your Name]."
    " For any inquiries, please reach out via [LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) or [GitHub](https://github.com/your-github-profile)."
)
