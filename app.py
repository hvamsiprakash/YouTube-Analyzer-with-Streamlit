# Importing necessary libraries and modules
import joblib
import streamlit as st
import googleapiclient.discovery
from textblob import TextBlob
import plotly.express as px
from transformers import pipeline
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyDm2xduRiZ1bsm9T7QjWehmNE95_4WR9KY"


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

# Function to perform sentiment analysis and categorize comments
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

# Function to generate a summary of comments using transformers
def generate_summary(comments):
    summarizer = pipeline("summarization")
    concatenated_comments = " ".join(comments)
    summary = summarizer(concatenated_comments, max_length=150, min_length=50, length_penalty=2.0)[0]['summary']
    return summary

# Function to generate word cloud based on comments
def generate_word_cloud(comments):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(" ".join(comments))
    keywords = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]

    # Generating Word Cloud
    wordcloud = WordCloud(width=800, height=400, background_color='black').generate(" ".join(keywords))

    # Display Word Cloud
    st.subheader("Word Cloud")
    st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)

# Streamlit web app
st.set_page_config(
    page_title="YouTube Video Analyzer",
    page_icon="📺",
    layout="wide"
)

# Set up the layout
st.title("YouTube Video Analyzer")
st.info(
    "This app allows you to perform various analysis tasks on YouTube videos. "
    "Select a task from the sidebar to get started."
)

# Sidebar for user input
st.sidebar.header("Select Task")

# Task selection
task = st.sidebar.selectbox("Task", ["Search Video Details", "Sentiment Analysis", "Summarization", "Word Cloud"])

# Search Video Details Task
if task == "Search Video Details":
    st.sidebar.info("Enter the topic to search for videos:")
    search_query = st.sidebar.text_input("Topic", value="Python Tutorial")

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

# Other Tasks
else:
    # User input for other tasks
    st.sidebar.header("Task Details")
    video_id = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

    if task == "Sentiment Analysis":
        st.sidebar.info("Analyze the sentiment of comments for a YouTube video.")
        if st.sidebar.button("Analyze Sentiments"):
            comments_sentiment = get_video_comments(video_id)
            categorized_sentiments = analyze_and_categorize_comments(comments_sentiment)
            st.subheader("Sentiment Analysis Results")
            for sentiment, comments in categorized_sentiments.items():
                st.write(f"**{sentiment} Sentiments:**")
                for comment in comments:
                    st.write(comment[0])
                st.write("---")

    elif task == "Summarization":
        st.sidebar.info("Generate a summary of the transcript or comments of a YouTube video using transformers.")
        if st.sidebar.button("Generate Summary"):
            comments_summary = get_video_comments(video_id)
            st.subheader("Summary Generation Task")
            generated_summary = generate_summary(comments_summary)
            st.write(generated_summary)

    elif task == "Word Cloud":
        st.sidebar.info("Generate a word cloud based on comments.")
        if st.sidebar.button("Generate Word Cloud"):
            comments_wordcloud = get_video_comments(video_id)
            st.subheader("Word Cloud Generation Task")
            generate_word_cloud(comments_wordcloud)

# Credits
st.title("Credits")
st.info(
    "This Streamlit app was created by [Your Name]."
)

# Footer
st.title("Connect with Me")
st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)

