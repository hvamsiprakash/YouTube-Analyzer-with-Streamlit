# # Importing necessary libraries and modules
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from textblob import TextBlob

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         channel_info = response.get("items", [])[0]["snippet"]
#         statistics_info = response.get("items", [])[0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, country, total_videos, total_views, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics,snippet",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             snippet_info = video_info.get("items", [])[0]["snippet"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))
#             comments = int(statistics_info.get("commentCount", 0))
#             upload_date = snippet_info.get("publishedAt", "N/A")
#             channel_name = snippet_info.get("channelTitle", "N/A")
#             thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")

#             video_details.append((title, video_id, likes, views, comments, upload_date, channel_name, url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Video ID", "Likes", "Views", "Comments", "Upload Date", "Channel", "URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Video ID", "Likes", "Views", "Comments", "Upload Date", "Channel", "URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=10):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="viewCount"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics,snippet",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             snippet_info = video_info.get("items", [])[0]["snippet"]
#             views = int(statistics_info.get("viewCount", 0))
#             channel_name = snippet_info.get("channelTitle", "N/A")
#             thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")
#             comments = int(statistics_info.get("commentCount", 0))  # Include total comments

#             video_details.append((title, video_id, views, channel_name, url, thumbnail_url, comments))  # Include total comments

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': [], 'Neutral': [], 'Negative': []}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
#             else:
#                 categorized_comments['Negative'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': [], 'Neutral': [], 'Negative': []}

# # Main Streamlit app
# st.title("Welcome to YouTube Analyzer!")

# # Description of the YouTube Analyzer app
# st.markdown(
#     """
#     🚀 Explore the fascinating world of YouTube with our Analyzer tool! Dive into detailed channel analytics, 
#     discover top video recommendations, and unravel the sentiment hidden in comments. 
#     Get ready for an interactive journey with vibrant charts and insightful statistics. 
#     Let's embark on the YouTube adventure together! 🎉
#     """
# )
# # Warning about YouTube API key
# st.warning(
#     """
#     ⚠️ **Important Notice:** The YouTube Data API key used in this app is for demonstration purposes only.
#     It may expire or reach its usage limit, resulting in errors. 
#     Replace it with your own API key to ensure uninterrupted access to YouTube data. 
#     Follow the instructions in the app's documentation to obtain and set up your API key.
#     """
# )
# # Note about using YouTube IDs
# st.info(
#     """
#     🚀 **Pro Tip:** To unlock the full power of YouTube Analyzer, use valid YouTube IDs for channels and videos!
#     Input a valid Channel ID to unleash comprehensive analytics, or enter an exciting Video ID to discover sentiment and more.
#     Get ready to embark on a thrilling journey of insights and exploration with YouTube IDs!
#     """
# )


# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, country, total_videos, total_views, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Views Over Time for Each Video", hover_data=["Title", "Likes", "Comments"])
#         fig_views.update_layout(height=600, width=1000, hovermode="x unified")  # Increased size for better visibility
#         st.plotly_chart(fig_views, use_container_width=True)

#         # Bar Chart for Likes and Comments
#         fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
#                                     title="Likes and Comments Comparison for Each Video", barmode="group", hover_data=["Title", "Views"])
#         fig_likes_comments.update_layout(height=600, width=1000, hovermode="x unified")  # Increased size for better visibility
#         st.plotly_chart(fig_likes_comments, use_container_width=True)

#         # New Chart: Scatter Plot for Likes vs Views
#         fig_likes_views = px.scatter(videos_df, x="Likes", y="Views", color="Channel",
#                                      title="Scatter Plot for Likes vs Views Across Videos", hover_data=["Title"])
#         fig_likes_views.update_layout(height=600, width=1000, hovermode="closest")  # Increased size for better visibility
#         st.plotly_chart(fig_likes_views, use_container_width=True)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: f"<a href='{x}' target='_blank'>{x}</a>")
#         st.write(videos_df[['Title', 'Video ID', 'Likes', 'Views', 'Comments', 'Upload Date', 'Channel', 'URL']].to_html(escape=False), unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=10)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**{video[0]}**")
#             st.write(f"<img src='{video[5]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
#             st.write(f"Video ID: {video[1]}")
#             st.write(f"Views: {video[2]}")
#             st.write(f"Channel: {video[3]}")
#             st.write(f"Total Comments: {video[6]}")  # Display total comments
#             st.write(f"Watch Video: [Link]({video[4]})")
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="")

#     # Fetch video title for display
#     video_info = youtube.videos().list(
#         part="snippet",
#         id=video_id_sentiment
#     ).execute()

#     video_title = video_info.get("items", [])[0]["snippet"]["title"] if video_info.get("items") else "Video Title N/A"

#     # Display video title in the main interface
#     st.subheader(f"Sentimental Analysis for Video: {video_title}")

#     # Allow the user to choose the type of comments
#     selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

#     if st.sidebar.button("Analyze Sentiments"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Analyze and categorize comments sentiment for all comments
#         categorized_comments_all = analyze_and_categorize_comments(comments_sentiment)

#         # Filter comments based on the selected sentiment
#         filtered_comments = categorized_comments_all.get(selected_sentiment, [])

#         # Display video title and visualization charts
#         st.subheader("Video Information")
#         st.write(f"**Video Title:** {video_title}")

#         # Visualization Chart 1: Bar Chart for Sentiment Distribution with Differentiated Colors
#         colors = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}

#         all_comments_count = [len(categorized_comments_all[sentiment]) for sentiment in ["Positive", "Neutral", "Negative"]]
#         all_sentiments = ["Positive", "Neutral", "Negative"]
#         fig_sentiment_bar_chart = px.bar(x=all_sentiments,
#                                          y=all_comments_count,
#                                          color=all_sentiments,
#                                          color_discrete_map=colors,
#                                          labels={"x": "Sentiment Type", "y": "Number of Comments"},
#                                          title=f"Sentiment Distribution for All Comments",
#                                          height=400)
#         st.plotly_chart(fig_sentiment_bar_chart, use_container_width=True)

#         # Visualization Chart 2: Scatter Plot for Relationship between Polarity and Subjectivity for All Comments
#         all_comments_polarity = []
#         all_comments_subjectivity = []

#         for sentiment_type in categorized_comments_all.values():
#             for comment_info in sentiment_type:
#                 all_comments_polarity.append(comment_info[1])
#                 all_comments_subjectivity.append(comment_info[2])

#         fig_scatter_plot_all = px.scatter(x=all_comments_polarity,
#                                           y=all_comments_subjectivity,
#                                           color=[selected_sentiment] * len(all_comments_polarity),
#                                           labels={"x": "Polarity", "y": "Subjectivity"},
#                                           title=f"Relationship between Polarity and Subjectivity ",
#                                           height=400)
#         st.plotly_chart(fig_scatter_plot_all, use_container_width=True)

#         # Display sentiment analysis results for the selected sentiment type
#         st.subheader(f"Selected Sentiment Type: {selected_sentiment}")
#         st.write(f"Total {selected_sentiment} Comments: {len(filtered_comments)}")

#         # Additional code for displaying comments
#         st.subheader(f"{selected_sentiment} Comments:")
#         for idx, comment_info in enumerate(filtered_comments[:20]):
#             comment_text, polarity, subjectivity = comment_info
#             st.write(f"{idx + 1}. {comment_text} (Polarity: {polarity}, Subjectivity: {subjectivity})")

# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/hvamsi/) | "
#     "[GitHub](https://github.com/hvamsiprakash)"
# )


import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Initialize the YouTube Data API client
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Set page config
st.set_page_config(
    page_title="YouTube Creator Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #1A1D23;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FF4B4B !important;
    }
    .st-bq {
        border-left-color: #FF4B4B;
    }
    .css-1aumxhk {
        background-color: #1A1D23;
        border-color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# Function to get channel analytics
def get_channel_analytics(channel_id):
    try:
        # Get channel stats
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        
        channel_info = channel_response.get("items", [])[0]
        snippet = channel_info["snippet"]
        stats = channel_info["statistics"]
        branding = channel_info.get("brandingSettings", {})
        
        # Get all videos
        videos = []
        next_page_token = None
        
        while True:
            search_response = youtube.search().list(
                channelId=channel_id,
                type="video",
                part="id",
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            
            if video_ids:
                videos_response = youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(video_ids)
                ).execute()
                
                videos.extend(videos_response.get("items", []))
            
            next_page_token = search_response.get("nextPageToken")
            if not next_page_token:
                break
        
        # Process video data
        video_data = []
        for video in videos:
            snippet = video["snippet"]
            stats = video["statistics"]
            details = video["contentDetails"]
            
            duration = details["duration"]
            # Convert ISO 8601 duration to minutes
            duration_min = convert_duration(duration)
            
            video_data.append({
                "title": snippet["title"],
                "video_id": video["id"],
                "published_at": snippet["publishedAt"],
                "duration": duration_min,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "engagement": (int(stats.get("likeCount", 0)) + int(stats.get("commentCount", 0))) / max(1, int(stats.get("viewCount", 1))) * 100
            })
        
        df = pd.DataFrame(video_data)
        df['published_at'] = pd.to_datetime(df['published_at'])
        df['month_year'] = df['published_at'].dt.to_period('M').astype(str)
        
        return {
            "channel_title": snippet["title"],
            "description": snippet["description"],
            "custom_url": branding.get("channel", {}).get("customUrl", ""),
            "thumbnail": snippet["thumbnails"]["high"]["url"],
            "country": snippet.get("country", "Not specified"),
            "published_at": snippet["publishedAt"],
            "subscribers": int(stats["subscriberCount"]),
            "total_views": int(stats["viewCount"]),
            "total_videos": int(stats["videoCount"]),
            "videos": df,
            "playlists": get_channel_playlists(channel_id)
        }
    except Exception as e:
        st.error(f"Error fetching channel analytics: {str(e)}")
        return None

def convert_duration(duration):
    # Convert ISO 8601 duration to minutes
    duration = duration.replace('PT', '').replace('H', ':').replace('M', ':').replace('S', '')
    parts = duration.split(':')
    
    if len(parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = parts
    elif len(parts) == 2:  # MM:SS
        hours = 0
        minutes, seconds = parts
    else:  # SS
        hours, minutes = 0, 0
        seconds = parts[0]
    
    return int(hours) * 60 + int(minutes) + (int(seconds) / 60)

def get_channel_playlists(channel_id):
    try:
        playlists = []
        next_page_token = None
        
        while True:
            response = youtube.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in response.get("items", []):
                playlists.append({
                    "title": item["snippet"]["title"],
                    "id": item["id"],
                    "item_count": item["contentDetails"]["itemCount"],
                    "published_at": item["snippet"]["publishedAt"]
                })
            
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        return playlists
    except Exception as e:
        st.error(f"Error fetching playlists: {str(e)}")
        return []

def calculate_earnings(views, currency="USD"):
    # Simplified earnings calculation (CPM ranges based on typical YouTube rates)
    # Note: Actual earnings vary widely based on content type, audience, etc.
    cpm_ranges = {
        "low": 0.5,   # Low end CPM ($0.5 per 1000 views)
        "medium": 2.5, # Average CPM
        "high": 10    # High end CPM for premium content
    }
    
    # Conversion rates (example values)
    conversion_rates = {
        "USD": 1,
        "INR": 75,
        "EUR": 0.85,
        "GBP": 0.75,
        "JPY": 110
    }
    
    earnings = {
        "low": (views / 1000) * cpm_ranges["low"] * conversion_rates.get(currency, 1),
        "medium": (views / 1000) * cpm_ranges["medium"] * conversion_rates.get(currency, 1),
        "high": (views / 1000) * cpm_ranges["high"] * conversion_rates.get(currency, 1)
    }
    
    return earnings

# Dashboard Layout
st.title("YouTube Creator Dashboard")

# Sidebar for inputs
with st.sidebar:
    st.header("Channel Configuration")
    channel_id = st.text_input("Enter YouTube Channel ID", key="channel_id")
    
    if channel_id:
        st.markdown("---")
        st.header("Display Options")
        time_range = st.selectbox(
            "Time Range",
            ["All Time", "Last Year", "Last 6 Months", "Last 3 Months"],
            index=0
        )
        
        currency = st.selectbox(
            "Earnings Currency",
            ["USD", "INR", "EUR", "GBP", "JPY"],
            index=0
        )
        
        earnings_scenario = st.selectbox(
            "Earnings Scenario",
            ["Conservative (Low CPM)", "Average (Medium CPM)", "Optimistic (High CPM)"],
            index=1
        )

# Main Dashboard
if channel_id:
    data = get_channel_analytics(channel_id)
    
    if data:
        # Apply time filter
        if time_range != "All Time":
            cutoff_date = {
                "Last Year": pd.Timestamp.now() - pd.DateOffset(years=1),
                "Last 6 Months": pd.Timestamp.now() - pd.DateOffset(months=6),
                "Last 3 Months": pd.Timestamp.now() - pd.DateOffset(months=3)
            }[time_range]
            
            data["videos"] = data["videos"][data["videos"]["published_at"] >= cutoff_date]
        
        # Header with channel info
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(data["thumbnail"], width=150)
        
        with col2:
            st.markdown(f"### {data['channel_title']}")
            st.markdown(f"**Custom URL:** [{data['custom_url']}](https://youtube.com/{data['custom_url']})")
            st.markdown(f"**Country:** {data['country']}")
            st.markdown(f"**Channel Created:** {pd.to_datetime(data['published_at']).strftime('%B %d, %Y')}")
        
        st.markdown("---")
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("### Subscribers")
            st.markdown(f"<h1 style='color:#FF4B4B;'>{data['subscribers']:,}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Total Views")
            st.markdown(f"<h1 style='color:#FF4B4B;'>{data['total_views']:,}</h1>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("### Videos")
            st.markdown(f"<h1 style='color:#FF4B4B;'>{data['total_videos']:,}</h1>", unsafe_allow_html=True)
        
        with col4:
            avg_engagement = data["videos"]["engagement"].mean()
            st.markdown("### Avg. Engagement Rate")
            st.markdown(f"<h1 style='color:#FF4B4B;'>{avg_engagement:.1f}%</h1>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # First Row: Views and Earnings
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Views Over Time")
            
            views_by_month = data["videos"].groupby("month_year")["views"].sum().reset_index()
            
            fig = px.line(
                views_by_month,
                x="month_year",
                y="views",
                labels={"month_year": "Month", "views": "Total Views"},
                line_shape="spline",
                render_mode="svg"
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                hovermode="x unified"
            )
            
            fig.update_traces(line=dict(color="#FF4B4B", width=3))
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Estimated Earnings")
            
            # Calculate earnings
            total_views = views_by_month["views"].sum()
            earnings = calculate_earnings(total_views, currency)
            
            scenario_map = {
                "Conservative (Low CPM)": "low",
                "Average (Medium CPM)": "medium",
                "Optimistic (High CPM)": "high"
            }
            
            selected_earnings = earnings[scenario_map[earnings_scenario]]
            
            st.markdown(f"<h2 style='color:#FF4B4B;'>{currency} {selected_earnings:,.2f}</h2>", unsafe_allow_html=True)
            st.markdown(f"*Based on {earnings_scenario.lower()}*")
            
            # Earnings breakdown by month
            monthly_earnings = views_by_month.copy()
            monthly_earnings["earnings"] = monthly_earnings["views"].apply(
                lambda x: (x / 1000) * 
                {"low": 0.5, "medium": 2.5, "high": 10}[scenario_map[earnings_scenario]] * 
                {"USD": 1, "INR": 75, "EUR": 0.85, "GBP": 0.75, "JPY": 110}[currency]
            )
            
            fig = px.bar(
                monthly_earnings,
                x="month_year",
                y="earnings",
                labels={"month_year": "Month", "earnings": f"Earnings ({currency})"},
                text=[f"{x:,.0f}" for x in monthly_earnings["earnings"]]
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                hovermode="x unified"
            )
            
            fig.update_traces(marker_color="#FF4B4B")
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Second Row: Top Videos and Engagement
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Top Performing Videos")
            
            top_videos = data["videos"].sort_values("views", ascending=False).head(5)
            
            for idx, row in top_videos.iterrows():
                st.markdown(f"""
                <div style="background-color:#1A1D23; padding:10px; border-radius:5px; margin-bottom:10px;">
                    <h4>{row['title']}</h4>
                    <p>📅 {pd.to_datetime(row['published_at']).strftime('%b %d, %Y')} | ⏱ {int(row['duration'])} min</p>
                    <p>👁️ {row['views']:,} views | 👍 {row['likes']:,} likes | 💬 {row['comments']:,} comments</p>
                    <p>Engagement Rate: {row['engagement']:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Engagement Analysis")
            
            # Engagement scatter plot
            fig = px.scatter(
                data["videos"],
                x="views",
                y="engagement",
                size="likes",
                color="engagement",
                color_continuous_scale=px.colors.sequential.Reds,
                hover_name="title",
                labels={"views": "Total Views", "engagement": "Engagement Rate (%)", "likes": "Likes Count"}
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Third Row: Content Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Video Duration Distribution")
            
            fig = px.histogram(
                data["videos"],
                x="duration",
                nbins=20,
                labels={"duration": "Duration (minutes)"},
                color_discrete_sequence=["#FF4B4B"]
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Playlist Overview")
            
            if data["playlists"]:
                playlists_df = pd.DataFrame(data["playlists"])
                playlists_df["published_at"] = pd.to_datetime(playlists_df["published_at"])
                
                fig = px.bar(
                    playlists_df.sort_values("item_count", ascending=False).head(5),
                    x="title",
                    y="item_count",
                    labels={"title": "Playlist Name", "item_count": "Number of Videos"},
                    color_discrete_sequence=["#FF4B4B"]
                )
                
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No playlists found for this channel.")
        
        st.markdown("---")
        
        # Raw Data
        if st.checkbox("Show Raw Video Data"):
            st.dataframe(data["videos"].sort_values("views", ascending=False))
else:
    st.info("Please enter a YouTube Channel ID in the sidebar to begin analysis.")

# Footer
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    YouTube Creator Dashboard • Data provided by YouTube API
</div>
""", unsafe_allow_html=True)
