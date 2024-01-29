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

# Main Streamlit app
st.title("YouTube Analyzer")

# Sidebar
st.sidebar.title("YouTube Analyzer")
st.sidebar.subheader("Select a Task")

# Task 1: Channel Analytics
if st.sidebar.checkbox("Channel Analytics"):
    st.sidebar.subheader("Channel Analytics")
    channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="UC4JX40jDee_tINbkjycV4Sg")

    if st.sidebar.button("Get Channel Analytics"):
        channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id_analytics)

        if channel_title:
            # Display Channel Analytics
            st.header("Channel Analytics")
            st.subheader(f"Channel: {channel_title}")
            st.write(f"Description: {description}")
            st.write(f"Published At: {published_at}")
            st.write(f"Country: {country}")
            st.write(f"Total Videos: {total_videos}")
            st.write(f"Total Views: {total_views}")
            st.write(f"Total Likes: {total_likes}")
            st.write(f"Total Comments: {total_comments}")

            # Display all video details in a dataframe
            st.subheader("All Video Details")
            st.dataframe(videos_df.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False), unsafe_allow_html=True)

# Task 2: Sentimental Analysis
if st.sidebar.checkbox("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID for Sentimental Analysis", value="QouN2F_gDmM")

    if st.sidebar.button("Get Sentimental Analysis"):
        comments_sentiment = get_video_comments(video_id_sentiment)

        if comments_sentiment:
            # Display Sentimental Analysis
            st.header("Sentimental Analysis")
            st.subheader(f"Video ID: {video_id_sentiment}")

            # Perform sentiment analysis on comments
            sentiments = [TextBlob(comment).sentiment.polarity for comment in comments_sentiment]

            # Plot sentiment distribution
            st.subheader("Sentiment Distribution of Comments")
            fig_polarity = px.bar(x=['Negative', 'Neutral', 'Positive'], y=[len([s for s in sentiments if s < 0]),
                                                                         len([s for s in sentiments if s == 0]),
                                                                         len([s for s in sentiments if s > 0])],
                                  labels={'x': 'Sentiment', 'y': 'Count'}, text=[f'{round((len([s for s in sentiments if s < 0]) / len(sentiments)) * 100, 2)}%',
                                                                             f'{round((len([s for s in sentiments if s == 0]) / len(sentiments)) * 100, 2)}%',
                                                                             f'{round((len([s for s in sentiments if s > 0]) / len(sentiments)) * 100, 2)}%'],
                                  title='Sentiment Distribution of Comments', color_discrete_sequence=['red', 'gray', 'green'])
            fig_polarity.update_traces(textposition='outside')
            st.plotly_chart(fig_polarity)

# Task 3: Video Recommendations
if st.sidebar.checkbox("Video Recommendations"):
    st.sidebar.subheader("Video Recommendations")
    topic_interest = st.sidebar.text_input("Enter Topic of Interest", "Python Programming")

    if st.sidebar.button("Get Video Recommendations"):
        video_recommendations = get_video_recommendations(topic_interest, max_results=5)

        if video_recommendations:
            # Display Video Recommendations
            st.header("Video Recommendations")
            st.subheader(f"Top 5 Videos on {topic_interest}")

            for video in video_recommendations:
                st.subheader(video[0])
                st.write(f"Views: {video[1]} | Likes: {video[2]}")
                st.write(f"Video URL: {video[3]}")



# Main Interface Paragraphs
st.markdown(
    """
    Welcome to YouTube Analyzer! This tool provides insights into YouTube channels, video recommendations, 
    and sentiment analysis of video comments. Use the sidebar to navigate through different tasks.
    """
)

# Task 1: Channel Analytics (Continued)
if channel_title:
    # More Advanced Charts for Channel Analytics
    st.subheader("Advanced Channel Analytics Charts")
    
    # Time Series Chart - Views Over Time
    st.write("Time Series Chart - Views Over Time")
    time_series_views = px.line(videos_df, x='Published At', y='View Count', title='Views Over Time', labels={'View Count': 'Views'})
    st.plotly_chart(time_series_views)

    # Additional Advanced Charts...

    # List all videos in a dataframe with clickable URLs
    st.subheader("All Video Details (Clickable URLs)")
    st.dataframe(videos_df.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False), unsafe_allow_html=True)

# Task 2: Sentimental Analysis (Continued)
if st.sidebar.checkbox("Sentimental Analysis"):
    # Additional Visualization Charts
    st.subheader("Additional Sentimental Analysis Charts")

    # Add more charts as per your requirements...
    # For example, a polarity chart
    st.write("Polarity Chart")
    fig_polarity_additional = px.pie(names=['Negative', 'Neutral', 'Positive'], values=[len([s for s in sentiments if s < 0]),
                                                                                         len([s for s in sentiments if s == 0]),
                                                                                         len([s for s in sentiments if s > 0])],
                                    title='Polarity Distribution of Comments', color_discrete_sequence=['red', 'gray', 'green'])
    st.plotly_chart(fig_polarity_additional)

# Task 3: Video Recommendations (Continued)
if st.sidebar.checkbox("Video Recommendations"):
    # Display thumbnails and details for recommended videos
    st.subheader("Recommended Videos (With Thumbnails)")

    for video in video_recommendations:
        thumbnail_url = get_thumbnail_url(video[3])
        if thumbnail_url:
            st.image(thumbnail_url, caption=f"Video URL: {video[3]}", use_container_width=True)

# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/hvamsi/) | "
    "[GitHub](https://github.com/hvamsiprakash)"
)


# Run the Streamlit app
if __name__ == '__main__':
    main()


