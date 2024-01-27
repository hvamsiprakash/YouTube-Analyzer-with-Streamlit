import joblib
import streamlit as st
import googleapiclient.discovery
from textblob import TextBlob
import plotly.express as px
from transformers import pipeline

# Set your YouTube Data API key here
YOUTUBE_API_KEY =  "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to search for videos and retrieve video details sorted by views
def search_and_recommend_videos(query, max_results=10):
    try:
        response = youtube.search().list(
            q=query,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            videoCaption="any",
            order="viewCount"  # Sort by views
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]

            # Use a separate request to get video statistics and content details
            video_info = youtube.videos().list(
                part="statistics,contentDetails,snippet",
                id=video_id
            ).execute()

            snippet_info = video_info.get("items", [])[0]["snippet"]
            statistics_info = video_info.get("items", [])[0]["statistics"]
            content_details = video_info.get("items", [])[0].get("contentDetails", {})

            likes = int(statistics_info.get("likeCount", 0))
            views = int(statistics_info.get("viewCount", 0))
            comments = int(statistics_info.get("commentCount", 0))
            duration = content_details.get("duration", "N/A")
            upload_date = snippet_info.get("publishedAt", "N/A")
            channel_title = snippet_info.get("channelTitle", "N/A")
            thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")

            link = f"https://www.youtube.com/watch?v={video_id}"

            video_details.append((title, video_id, likes, views, comments, duration, upload_date, channel_title, link, thumbnail_url))

        return video_details
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching videos: {e}")
        return []

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

# Streamlit web app
st.set_page_config(
    page_title="YouTube Video Analyzer",
    page_icon="📺",
    layout="wide"
)

st.title("YouTube Video Analyzer")

# Sidebar for user input
st.sidebar.header("Select Task")

task = st.sidebar.selectbox("Task", ["Search Video Details", "Sentiment Analysis", "Summary Generation", "Keyword Extraction and Word Cloud", "Abuse and Spam Detection"])

search_query = st.sidebar.text_input("Enter the topic of interest", value="Python Tutorial")

if st.sidebar.button("Search"):
    video_details = search_and_recommend_videos(search_query)
    st.subheader("Search Results:")
    if video_details:
        for video in video_details:
            st.write(f"**{video[0]}**")
            st.write(f"<img src='{video[9]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
            st.write(f"Likes: {video[2]}, Views: {video[3]}, Comments: {video[4]}, Duration: {video[5]}, Upload Date: {video[6]}, Channel: {video[7]}")
            st.write(f"Watch [video]({video[8]})")
            st.write("---")
    else:
        st.warning("No videos found.")

# Main content based on selected task
if task == "Sentiment Analysis":
    st.sidebar.header("Sentiment Analysis Task")
    st.sidebar.info(
        "This task allows you to analyze the sentiment of comments for a YouTube video."
        " Enter the video ID below and click the button to get sentiment analysis results."
    )

    # User input for sentiment analysis task
    video_id_sentiment = st.sidebar.text_input("Enter Video ID for Sentiment Analysis", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Analyze Sentiments"):
        # Get comments for sentiment analysis
        comments_sentiment = get_video_comments(video_id_sentiment)

        # Analyze and categorize comments
        categorized_sentiments = analyze_and_categorize_comments(comments_sentiment)

        st.subheader("Sentiment Analysis Results")

        # Display results
        for sentiment, comments in categorized_sentiments.items():
            st.write(f"**{sentiment} Sentiments:**")
            for comment in comments:
                st.write(comment[0])
            st.write("---")

elif task == "Summary Generation":
    st.sidebar.header("Summary Generation Task")
    st.sidebar.info(
        "This task allows you to generate a summary of the transcript of a YouTube video using transformers."
        " Enter the video ID below and click the button to generate a summary."
    )

    # User input for summary generation task
    video_id_summary = st.sidebar.text_input("Enter Video ID for Summary Generation", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Generate Summary"):
        # Get comments for summary generation
        comments_summary = get_video_comments(video_id_summary)

        st.subheader("Summary Generation Task")

        # Placeholder for summary generation logic
        st.warning("Summary Generation logic is a placeholder and needs to be implemented.")

elif task == "Keyword Extraction and Word Cloud":
    st.sidebar.header("Keyword Extraction and Word Cloud Task")
    st.sidebar.info(
        "This task allows you to extract keywords from comments and generate a word cloud."
        " Enter the video ID below and click the button to perform keyword extraction and generate a word cloud."
    )

    # User input for keyword extraction task
    video_id_keywords = st.sidebar.text_input("Enter Video ID for Keyword Extraction", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Extract Keywords and Generate Word Cloud"):
        # Get comments for keyword extraction
        comments_keywords = get_video_comments(video_id_keywords)

        st.subheader("Keyword Extraction and Word Cloud Generation Task")

        # Placeholder for keyword extraction and word cloud logic
        st.warning("Keyword Extraction and Word Cloud logic are placeholders and need to be implemented.")

elif task == "Abuse and Spam Detection":
    st.sidebar.header("Abuse and Spam Detection Task")
    st.sidebar.info(
        "This task implements deep learning models to detect and filter out abusive or spammy comments,"
        " ensuring a more positive user experience on the platform."
        " Enter the video ID below and click the button to detect abuse and spam."
    )

    # User input for abuse and spam detection task
    video_id_abuse_spam = st.sidebar.text_input("Enter Video ID for Abuse and Spam Detection", value="YOUR_VIDEO_ID")

    if st.sidebar.button("Detect Abuse and Spam"):
        # Get comments for abuse and spam detection
        comments_abuse_spam = get_video_comments(video_id_abuse_spam)

        st.subheader("Abuse and Spam Detection Task")

        # Placeholder for abuse and spam detection logic
        st.warning("Abuse and Spam Detection logic is a placeholder and needs to be implemented.")

# Set up the layout
st.sidebar.title("About")
st.sidebar.info(
    "This app allows you to perform various analysis tasks on YouTube videos. "
    "Select a task from the sidebar to get started."
)

# Credits
st.sidebar.title("Credits")
st.sidebar.info(
    "This Streamlit app was created by [Your Name]. You can find the source code on [GitHub Repo Link]."
)

# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)
