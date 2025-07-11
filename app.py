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



# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Creator Pro Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
def set_dark_theme():
    st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #0E1117;
        color: white;
        border-right: 1px solid #333;
    }
    .st-bw {
        background-color: #0E1117;
    }
    .st-at {
        background-color: #262730;
    }
    .css-1aumxhk {
        background-color: #0E1117;
        background-image: none;
        color: white;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FF4B4B !important;
    }
    .css-1v0mbdj {
        border: 1px solid #333;
    }
    .st-bq {
        color: white;
    }
    .st-cn {
        background-color: #262730;
    }
    </style>
    """, unsafe_allow_html=True)

set_dark_theme()

# Function to get comprehensive channel analytics
def get_channel_analytics(channel_id):
    try:
        # Get channel statistics
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        
        if not channel_response.get("items"):
            st.error("Channel not found. Please check the Channel ID.")
            return None
            
        channel_info = channel_response["items"][0]
        
        # Get channel videos
        videos_response = youtube.search().list(
            channelId=channel_id,
            type="video",
            part="id,snippet",
            maxResults=50,
            order="date"
        ).execute()
        
        video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]
        
        # Get detailed video statistics
        videos_data = []
        for video_id in video_ids:
            video_response = youtube.videos().list(
                part="statistics,snippet,contentDetails",
                id=video_id
            ).execute()
            
            if video_response.get("items"):
                video = video_response["items"][0]
                stats = video["statistics"]
                snippet = video["snippet"]
                details = video["contentDetails"]
                
                videos_data.append({
                    "title": snippet.get("title", "N/A"),
                    "video_id": video_id,
                    "published_at": snippet.get("publishedAt", "N/A"),
                    "duration": details.get("duration", "N/A"),
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "engagement": (int(stats.get("likeCount", 0)) + int(stats.get("commentCount", 0))) / max(1, int(stats.get("viewCount", 1))),
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                })
        
        # Get channel playlists
        playlists_response = youtube.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50
        ).execute()
        
        playlists_data = []
        for playlist in playlists_response.get("items", []):
            playlists_data.append({
                "title": playlist["snippet"]["title"],
                "playlist_id": playlist["id"],
                "item_count": playlist["contentDetails"]["itemCount"],
                "thumbnail": playlist["snippet"]["thumbnails"]["high"]["url"]
            })
        
        # Format the data
        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "custom_url": channel_info["snippet"].get("customUrl", "N/A"),
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country", "N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"],
                "banner": channel_info["brandingSettings"].get("image", {}).get("bannerExternalUrl", "N/A")
            },
            "statistics": {
                "view_count": int(channel_info["statistics"]["viewCount"]),
                "subscriber_count": int(channel_info["statistics"]["subscriberCount"]),
                "video_count": int(channel_info["statistics"]["videoCount"]),
                "hidden_subscriber_count": channel_info["statistics"]["hiddenSubscriberCount"]
            },
            "videos": sorted(videos_data, key=lambda x: x["views"], reverse=True),
            "playlists": playlists_data
        }
        
        return channel_data
        
    except Exception as e:
        st.error(f"Error fetching channel data: {str(e)}")
        return None

# Function to calculate estimated earnings (simplified model)
def calculate_earnings(videos_data, currency="USD"):
    # Simplified RPM (Revenue Per Mille) estimates by category
    rpm_rates = {
        "USD": {"low": 1.5, "medium": 3.0, "high": 5.0},
        "INR": {"low": 110, "medium": 220, "high": 370},
        "EUR": {"low": 1.3, "medium": 2.7, "high": 4.5}
    }
    
    # Calculate total views
    total_views = sum(video["views"] for video in videos_data)
    
    # Calculate earnings based on RPM (using medium as default)
    rpm = rpm_rates[currency]["medium"]
    estimated_earnings = (total_views / 1000) * rpm
    
    # Monthly breakdown
    monthly_data = {}
    for video in videos_data:
        month = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
        if month not in monthly_data:
            monthly_data[month] = 0
        monthly_data[month] += video["views"]
    
    monthly_earnings = {month: (views/1000)*rpm for month, views in monthly_data.items()}
    
    return {
        "total_earnings": estimated_earnings,
        "monthly_earnings": monthly_earnings,
        "currency": currency,
        "rpm": rpm,
        "total_views": total_views
    }

# Function to format numbers
def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

# Main dashboard function
def youtube_dashboard():
    st.title("YouTube Creator Pro Dashboard")
    st.markdown("""
    <style>
    .metric-box {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #FF4B4B;
    }
    .metric-title {
        color: #FF4B4B;
        font-size: 14px;
        font-weight: bold;
    }
    .metric-value {
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("Dashboard Configuration")
    channel_id = st.sidebar.text_input("Enter YouTube Channel ID", key="channel_id")
    
    currency_options = {"USD": "US Dollar", "INR": "Indian Rupee", "EUR": "Euro"}
    selected_currency = st.sidebar.selectbox("Select Currency for Earnings", options=list(currency_options.keys()), 
                                           format_func=lambda x: currency_options[x])
    
    time_range = st.sidebar.selectbox("Time Range", ["Last 30 days", "Last 90 days", "Last 12 months", "All time"])
    
    if st.sidebar.button("Analyze Channel"):
        if not channel_id:
            st.error("Please enter a valid YouTube Channel ID")
            return
            
        with st.spinner("Fetching channel data..."):
            channel_data = get_channel_analytics(channel_id)
            
        if not channel_data:
            return
            
        # Calculate earnings
        earnings_data = calculate_earnings(channel_data["videos"], selected_currency)
        
        # Main dashboard layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Subscribers</div>
                <div class="metric-value">{format_number(channel_data['statistics']['subscriber_count'])}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Views</div>
                <div class="metric-value">{format_number(channel_data['statistics']['view_count'])}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Videos</div>
                <div class="metric-value">{format_number(channel_data['statistics']['video_count'])}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Estimated Earnings</div>
                <div class="metric-value">{selected_currency} {earnings_data['total_earnings']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Channel header
        st.markdown("---")
        col_header1, col_header2 = st.columns([1, 3])
        
        with col_header1:
            st.image(channel_data["basic_info"]["thumbnail"], width=150)
            
        with col_header2:
            st.markdown(f"### {channel_data['basic_info']['title']}")
            st.markdown(f"**Channel URL:** youtube.com/channel/{channel_id}")
            st.markdown(f"**Country:** {channel_data['basic_info']['country']}")
            st.markdown(f"**Created:** {datetime.strptime(channel_data['basic_info']['published_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')}")
        
        # First row of charts
        st.markdown("---")
        st.markdown("### Performance Overview")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Views over time
            df_views = pd.DataFrame({
                "Date": [datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ") for video in channel_data["videos"]],
                "Views": [video["views"] for video in channel_data["videos"]]
            })
            
            fig_views = px.line(df_views, x="Date", y="Views", 
                              title="Views Over Time",
                              color_discrete_sequence=["#FF4B4B"])
            fig_views.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", 
                                  font={"color": "white"}, hovermode="x unified")
            st.plotly_chart(fig_views, use_container_width=True)
            
        with col_chart2:
            # Monthly earnings
            df_earnings = pd.DataFrame({
                "Month": list(earnings_data["monthly_earnings"].keys()),
                "Earnings": list(earnings_data["monthly_earnings"].values())
            })
            
            fig_earnings = px.bar(df_earnings, x="Month", y="Earnings",
                                 title=f"Monthly Earnings ({selected_currency})",
                                 color_discrete_sequence=["#FF4B4B"])
            fig_earnings.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", 
                                     font={"color": "white"}, hovermode="x unified")
            st.plotly_chart(fig_earnings, use_container_width=True)
        
        # Second row of charts
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            # Top performing videos
            top_videos = sorted(channel_data["videos"], key=lambda x: x["views"], reverse=True)[:5]
            df_top_videos = pd.DataFrame({
                "Video": [video["title"] for video in top_videos],
                "Views": [video["views"] for video in top_videos]
            })
            
            fig_top_videos = px.bar(df_top_videos, x="Views", y="Video", orientation='h',
                                   title="Top Performing Videos by Views",
                                   color_discrete_sequence=["#FF4B4B"])
            fig_top_videos.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", 
                                      font={"color": "white"}, hovermode="y unified")
            st.plotly_chart(fig_top_videos, use_container_width=True)
            
        with col_chart4:
            # Engagement rate scatter plot
            df_engagement = pd.DataFrame({
                "Video": [video["title"] for video in channel_data["videos"]],
                "Views": [video["views"] for video in channel_data["videos"]],
                "Engagement": [video["engagement"]*100 for video in channel_data["videos"]],
                "Likes": [video["likes"] for video in channel_data["videos"]]
            })
            
            fig_engagement = px.scatter(df_engagement, x="Views", y="Engagement", size="Likes",
                                      title="Engagement Rate vs Views",
                                      color_discrete_sequence=["#FF4B4B"],
                                      hover_name="Video")
            fig_engagement.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", 
                                      font={"color": "white"}, hovermode="closest")
            st.plotly_chart(fig_engagement, use_container_width=True)
        
        # Video details section
        st.markdown("---")
        st.markdown("### Video Performance Details")
        
        # Create a DataFrame for the video data
        video_df = pd.DataFrame(channel_data["videos"])
        video_df["published_at"] = pd.to_datetime(video_df["published_at"])
        video_df["engagement_rate"] = video_df["engagement"] * 100
        
        # Add filters
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            min_views = st.slider("Minimum Views", 
                                 min_value=0, 
                                 max_value=int(video_df["views"].max()), 
                                 value=0)
            
        with col_filter2:
            min_likes = st.slider("Minimum Likes", 
                                 min_value=0, 
                                 max_value=int(video_df["likes"].max()), 
                                 value=0)
            
        with col_filter3:
            date_range = st.date_input("Date Range", 
                                     [video_df["published_at"].min(), 
                                     video_df["published_at"].max()])
        
        # Apply filters
        filtered_df = video_df[
            (video_df["views"] >= min_views) & 
            (video_df["likes"] >= min_likes) & 
            (video_df["published_at"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
        ]
        
        # Display filtered results
        st.dataframe(filtered_df[["title", "published_at", "views", "likes", "comments", "engagement_rate"]].rename(columns={
            "title": "Title",
            "published_at": "Published Date",
            "views": "Views",
            "likes": "Likes",
            "comments": "Comments",
            "engagement_rate": "Engagement Rate (%)"
        }), height=400)
        
        # Playlists section
        if channel_data["playlists"]:
            st.markdown("---")
            st.markdown("### Playlists Performance")
            
            for playlist in channel_data["playlists"]:
                col_pl1, col_pl2 = st.columns([1, 4])
                
                with col_pl1:
                    st.image(playlist["thumbnail"], width=150)
                    
                with col_pl2:
                    st.markdown(f"**{playlist['title']}**")
                    st.markdown(f"**Videos:** {playlist['item_count']}")
                    st.markdown(f"**Playlist ID:** {playlist['playlist_id']}")

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
