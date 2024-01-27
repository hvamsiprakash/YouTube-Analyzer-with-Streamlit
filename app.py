import joblib
import streamlit as st
import googleapiclient.discovery
from textblob import TextBlob
import plotly.express as px
from profanity_check import predict
from transformers import pipeline

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

# Placeholder function for sentiment analysis
def analyze_and_categorize_comments(comments):
    # Replace this placeholder with your actual sentiment analysis logic
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

# Task 1: Search Video Details
st.title("YouTube Video Analyzer")
st.sidebar.header("Task 1: Search Video Details")

search_query = st.sidebar.text_input("Enter the topic of interest", value="Python Tutorial")

if st.sidebar.button("Search"):
    video_details = search_and_recommend_videos(search_query)
    st.subheader("Search Results:")
    if video_details:
        for video in video_details:
            st.write(f"**{video[0]}**")
            st.write(f"<img src='{video[9]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
            st.write(f"Video ID: {video[1]}")
            st.write(f"Likes: {video[2]}, Views: {video[3]}, Comments: {video[4]}")
            st.write(f"Duration: {video[5]}, Upload Date: {video[6]}")
            st.write(f"Channel: {video[7]}")
            st.write(f"Watch Video: [Link]({video[8]})")

# Task 2: Sentiment Analysis
st.sidebar.header("Task 2: Sentiment Analysis")

video_id_sentiment = st.sidebar.text_input("Enter Video ID for Sentiment Analysis", value="YOUR_VIDEO_ID")

if st.sidebar.button("Analyze Sentiment"):
    comments_sentiment = get_video_comments(video_id_sentiment)
    st.subheader("Sentiment Analysis")

    # Check if there are comments before analysis
    if comments_sentiment:
        # Use the placeholder function for sentiment analysis
        categorized_comments_sentiment = analyze_and_categorize_comments(comments_sentiment)

        # Display additional metrics
        st.write(f"Total Comments: {len(comments_sentiment)}")
        st.write(f"Average Sentiment Polarity: {sum(s[1] for s in categorized_comments_sentiment['Positive'] + categorized_comments_sentiment['Negative']) / len(comments_sentiment)}")
        st.write(f"Average Sentiment Subjectivity: {sum(s[2] for s in categorized_comments_sentiment['Positive'] + categorized_comments_sentiment['Negative']) / len(comments_sentiment)}")

        # Display sentiment distribution chart
        sentiment_df = []
        for sentiment, sentiment_comments in categorized_comments_sentiment.items():
            sentiment_df.extend([(sentiment, comment[1], comment[2]) for comment in sentiment_comments])

        sentiment_chart = px.scatter(sentiment_df, x=1, y=2, color=0, labels={'1': 'Polarity', '2': 'Subjectivity'}, title='Sentiment Analysis')
        st.plotly_chart(sentiment_chart)

        # Display categorized comments
        for sentiment, sentiment_comments in categorized_comments_sentiment.items():
            st.subheader(sentiment)
            for comment in sentiment

_comments:
                st.write(f"- *Polarity*: {comment[1]}, *Subjectivity*: {comment[2]}")
                st.write(f"  {comment[0]}")

# Task 3: Named Entity Recognition (NER)
st.sidebar.header("Task 3: Named Entity Recognition (NER)")

video_id_ner = st.sidebar.text_input("Enter Video ID for NER", value="YOUR_VIDEO_ID")

if st.sidebar.button("Perform NER"):
    comments_ner = get_video_comments(video_id_ner)
    st.subheader("Named Entity Recognition (NER)")

    # Check if there are comments before NER
    if comments_ner:
        # Perform Named Entity Recognition (NER) using your NER logic here

        # Display NER results
        st.write("NER results will be displayed here.")

# Task 4: Summary Generation
st.sidebar.header("Task 4: Summary Generation")

video_id_summary = st.sidebar.text_input("Enter Video ID for Summary Generation", value="YOUR_VIDEO_ID")

if st.sidebar.button("Generate Summary"):
    comments_summary = get_video_comments(video_id_summary)
    st.subheader("Summary Generation")

    # Check if there are comments before summary generation
    if comments_summary:
        # Perform Summary Generation using transformers pipeline
        summarization_pipeline = pipeline("summarization")
        text_for_summary = " ".join(comments_summary)
        summary = summarization_pipeline(text_for_summary, max_length=150, min_length=50, length_penalty=2.0, num_beams=4)

        # Display generated summary
        st.write(f"**Generated Summary:**")
        st.write(summary[0]['summary_text'])

# Task 5: Abuse and Spam Detection
st.sidebar.header("Task 5: Abuse and Spam Detection")

# Placeholder function for abuse and spam detection
def detect_abuse_and_spam(comments):
    # Replace this placeholder with your actual abuse and spam detection logic
    detected_comments = [comment for comment in comments if predict(comment)]
    return detected_comments

video_id_abuse_spam = st.sidebar.text_input("Enter Video ID for Abuse and Spam Detection", value="YOUR_VIDEO_ID")

if st.sidebar.button("Detect Abuse and Spam"):
    comments_abuse_spam = get_video_comments(video_id_abuse_spam)
    st.subheader("Abuse and Spam Detection")

    # Check if there are comments before abuse and spam detection
    if comments_abuse_spam:
        # Use the placeholder function for abuse and spam detection
        detected_comments_abuse_spam = detect_abuse_and_spam(comments_abuse_spam)

        # Display detected abusive and spammy comments
        st.write(f"Detected Abusive and Spammy Comments:")
        for comment in detected_comments_abuse_spam:
            st.write(f"- {comment}")

# Task 6: Word Cloud Generation
st.sidebar.header("Task 6: Word Cloud Generation")

video_id_wordcloud = st.sidebar.text_input("Enter Video ID for Word Cloud Generation", value="YOUR_VIDEO_ID")

if st.sidebar.button("Generate Word Cloud"):
    comments_wordcloud = get_video_comments(video_id_wordcloud)
    st.subheader("Word Cloud Generation")

    # Check if there are comments before word cloud generation
    if comments_wordcloud:
        # Perform Word Cloud Generation using your logic here

        # Display generated word cloud
        st.write("Word cloud will be displayed here.")

# Sidebar: User Options for Sentiment Analysis
st.sidebar.header("User Options for Sentiment Analysis")

# Placeholder function for displaying user options
def display_user_options():
    # Replace this placeholder with your actual logic for user options
    pass

display_user_options()

# Sidebar: Python Dependencies
st.sidebar.header("Python Dependencies")

# Displaying Python dependencies
st.sidebar.code("""
google-api-python-client==2.24.0
textblob==0.15.3
wordcloud==1.8.1
matplotlib==3.5.1
streamlit==1.10.0
plotly==5.15.0
nltk==3.6.6
langdetect==1.0.9
scikit-learn==0.24.2
pandas==1.3.3
speechrecognition==3.8.1
moviepy==1.0.3
transformers==4.10.3
profanity-check==1.0.3
torch==1.10.1
""")

# Run the app
if __name__ == "__main__":
    st.run_app()
