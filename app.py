User
# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
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

# Function to generate word cloud from comments
def generate_word_cloud(comments):
    try:
        if not comments:
            st.warning("No comments to generate a word cloud.")
            return None

        text = " ".join(comments)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

        return wordcloud
    except Exception as e:
        st.error(f"Error generating word cloud: {e}")
        return None

# Function to analyze and categorize comments sentiment
def analyze_and_categorize_comments(comments):
    try:
        categorized_comments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

        for comment in comments:
            analysis = TextBlob(comment)
            # Classify the polarity of the comment
            if analysis.sentiment.polarity > 0:
                categorized_comments['Positive'] += 1
            elif analysis.sentiment.polarity == 0:
                categorized_comments['Neutral'] += 1
            else:
                categorized_comments['Negative'] += 1

        return categorized_comments
    except Exception as e:
        st.error(f"Error analyzing comments: {e}")
        return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

# Function to get user-selected comments based on sentiment
def get_user_selected_comments(comments, comment_type):
    try:
        selected_comments = []
        for comment in comments:
            analysis = TextBlob(comment)
            if comment_type == "positive" and analysis.sentiment.polarity > 0:
                selected_comments.append(comment)
            elif comment_type == "neutral" and analysis.sentiment.polarity == 0:
                selected_comments.append(comment)
            elif comment_type == "negative" and analysis.sentiment.polarity < 0:
                selected_comments.append(comment)

        return selected_comments
    except Exception as e:
        st.error(f"Error filtering user-selected comments: {e}")
        return []

# Main Streamlit app
st.set_page_config(page_title="YouTube Analyzer", page_icon=":movie_camera:", layout="wide")

# Main layout
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
        videos_df['URL'] = videos_df['URL'].apply(lambda x: f'<a href="{x}" target="_blank">Link</a>')
        st.dataframe(videos_df.style.format({'URL': '<a href="{}" target="_blank">Link</a>'}, escape=False), unsafe_allow_html=True)

# Task 2: Video Recommendation based on User's Topic of Interest
if st.sidebar.checkbox("Video Recommendation"):
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
if st.sidebar.checkbox("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

    # User selection for comment type
    comment_type = st.sidebar.radio(
        "Select the type of comments to analyze:",
        options=["All Comments", "Positive Comments", "Neutral Comments", "Negative Comments"]
    )

    # Fetch comments for the selected video
    video_comments = get_video_comments(video_id_sentiment)

    if video_comments:
        st.subheader("Sentimental Analysis of Comments")

        # Display user-selected comment type
        st.write(f"**Selected Comment Type:** {comment_type}")

        # Analyze and categorize comments sentiment
        categorized_comments = analyze_and_categorize_comments(video_comments)

        # Display sentiment distribution
        st.subheader("Sentiment Distribution of Comments")
        fig_polarity = px.bar(
            x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
            title="Sentiment Distribution of Comments", labels={"x": "Sentiment", "y": "Count"}
        )
        fig_polarity.update_layout(height=400, width=800)
        st.plotly_chart(fig_polarity)

        # User selection for additional visualization charts
        st.subheader("Additional Visualization Charts")

        if st.checkbox("Display Pie Chart for Sentiment Distribution"):
            fig_pie = px.pie(
                values=list(categorized_comments.values()), names=list(categorized_comments.keys()),
                title="Pie Chart for Sentiment Distribution"
            )
            st.plotly_chart(fig_pie)

        # Word Cloud for Comments
        if st.checkbox("Display Word Cloud for Comments"):
            wordcloud = generate_word_cloud(video_comments)
            if wordcloud:
                st.subheader("Word Cloud for Comments")
                st.image(wordcloud.to_array(), use_container_width=True)

        # User selection to display specific comment type
        if comment_type != "All Comments":
            selected_comments = get_user_selected_comments(video_comments, comment_type.lower())

            st.subheader(f"{comment_type.capitalize()} Comments")
            st.text_area("Selected Comments", "\n".join(selected_comments), height=200)
    else:
        st.warning("No comments available for sentiment analysis.")




# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/hvamsi/) | "
    "[GitHub](https://github.com/hvamsiprakash)"
)
