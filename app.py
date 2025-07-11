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

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Custom color palette
COLOR_PALETTE = {
    'background': '#0E1117',
    'text': '#FFFFFF',
    'primary': '#FF0000',
    'secondary': '#8B0000',
    'accent': '#FF4500',
    'card': '#1A1A1A'
}

# Set page config with dark theme
st.set_page_config(
    page_title="YouTube Creator Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for dark theme
def set_dark_theme():
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLOR_PALETTE['background']};
            color: {COLOR_PALETTE['text']};
        }}
        .css-1d391kg {{
            background-color: {COLOR_PALETTE['card']} !important;
        }}
        .st-bb {{
            background-color: {COLOR_PALETTE['card']};
        }}
        .st-at {{
            background-color: {COLOR_PALETTE['primary']};
        }}
        .css-1aumxhk {{
            color: {COLOR_PALETTE['text']};
        }}
        .css-qri22k {{
            background-color: {COLOR_PALETTE['card']};
        }}
        .css-12ttj6m {{
            background-color: {COLOR_PALETTE['secondary']};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {COLOR_PALETTE['primary']} !important;
        }}
        .css-1v3fvcr {{
            color: {COLOR_PALETTE['text']};
        }}
    </style>
    """, unsafe_allow_html=True)

set_dark_theme()

# Function to get comprehensive channel analytics
def get_channel_analytics(channel_id):
    try:
        # Get channel basic info
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        
        if not channel_response.get("items"):
            st.error("Channel not found. Please check the Channel ID.")
            return None
            
        channel_info = channel_response["items"][0]
        
        # Get uploads playlist ID
        uploads_playlist_id = channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get all videos from the uploads playlist
        videos = []
        next_page_token = None
        
        while True:
            playlist_response = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            videos.extend(playlist_response["items"])
            next_page_token = playlist_response.get("nextPageToken")
            
            if not next_page_token:
                break
        
        # Get video statistics for all videos
        video_ids = [video["contentDetails"]["videoId"] for video in videos]
        video_stats = []
        
        # Process in batches of 50 (YouTube API limit)
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            stats_response = youtube.videos().list(
                part="statistics,snippet,contentDetails",
                id=",".join(batch)
            ).execute()
            video_stats.extend(stats_response["items"])
        
        # Process all data into structured format
        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country", "N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"],
                "banner": channel_info["brandingSettings"]["image"].get("bannerExternalUrl", None) if "brandingSettings" in channel_info else None,
                "subscribers": int(channel_info["statistics"]["subscriberCount"]),
                "total_views": int(channel_info["statistics"]["viewCount"]),
                "total_videos": int(channel_info["statistics"]["videoCount"]),
                "hidden_subscriber": channel_info["statistics"].get("hiddenSubscriberCount", False)
            },
            "videos": []
        }
        
        for video in video_stats:
            stats = video["statistics"]
            snippet = video["snippet"]
            
            video_data = {
                "id": video["id"],
                "title": snippet["title"],
                "published_at": snippet["publishedAt"],
                "description": snippet["description"],
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "duration": video["contentDetails"]["duration"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "dislikes": int(stats.get("dislikeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "engagement": (int(stats.get("likeCount", 0)) + int(stats.get("commentCount", 0))) / max(1, int(stats.get("viewCount", 1))) * 100
            }
            channel_data["videos"].append(video_data)
        
        return channel_data
    
    except Exception as e:
        st.error(f"Error fetching channel analytics: {str(e)}")
        return None

# Function to calculate estimated earnings
def calculate_earnings(views, country="US"):
    # RPM (Revenue Per Mille) estimates by country (USD per 1000 views)
    rpm_by_country = {
        "US": 3.00, "CA": 2.50, "UK": 2.20, "DE": 2.00, "FR": 1.80,
        "AU": 2.30, "JP": 1.50, "IN": 0.50, "BR": 0.80, "RU": 0.70,
        "DEFAULT": 1.50  # Default RPM for other countries
    }
    
    rpm = rpm_by_country.get(country.upper(), rpm_by_country["DEFAULT"])
    estimated_earnings = (views / 1000) * rpm
    return estimated_earnings

# Function to convert earnings to prizes
def convert_to_prizes(amount, country="US"):
    # Some fun conversions to real-world items based on country
    conversions = {
        "US": [
            ("iPhone 14 Pro", 999),
            ("PlayStation 5", 499),
            ("50 Starbucks Coffees", 150),
            ("1 Month Rent (Avg)", 1500),
            ("Tesla Model 3", 40000)
        ],
        "UK": [
            ("iPhone 14 Pro", 999),
            ("PlayStation 5", 450),
            ("50 Costa Coffees", 120),
            ("1 Month Rent (Avg)", 1200),
            ("Mini Cooper", 25000)
        ],
        "IN": [
            ("iPhone 14 Pro", 120000),
            ("PlayStation 5", 50000),
            ("50 Chai Teas", 500),
            ("1 Month Rent (Avg)", 30000),
            ("Tata Nexon", 1000000)
        ],
        "DEFAULT": [
            ("iPhone 14 Pro", 1000),
            ("PlayStation 5", 500),
            ("50 Coffees", 150),
            ("1 Month Rent (Avg)", 1000),
            ("Average Car", 25000)
        ]
    }
    
    country_conversions = conversions.get(country.upper(), conversions["DEFAULT"])
    prizes = []
    
    for item, price in country_conversions:
        quantity = amount // price
        if quantity > 0:
            prizes.append(f"{int(quantity)} {item}{'s' if quantity > 1 else ''}")
    
    return prizes if prizes else ["Not enough for major purchases"]

# Function to format large numbers
def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

# Function to parse ISO 8601 duration
def parse_duration(duration):
    # Remove 'PT' prefix
    duration = duration[2:]
    hours = 0
    minutes = 0
    seconds = 0
    
    if 'H' in duration:
        hours_part = duration.split('H')[0]
        hours = int(hours_part)
        duration = duration.split('H')[1]
    
    if 'M' in duration:
        minutes_part = duration.split('M')[0]
        minutes = int(minutes_part)
        duration = duration.split('M')[1]
    
    if 'S' in duration:
        seconds_part = duration.split('S')[0]
        seconds = int(seconds_part)
    
    return hours * 3600 + minutes * 60 + seconds

# Main dashboard
def main():
    st.title("📊 YouTube Creator Dashboard")
    st.markdown("""
    <style>
    .big-font {
        font-size:18px !important;
        color: #FF0000 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="big-font">Advanced analytics for YouTube content creators</p>', unsafe_allow_html=True)
    
    # Sidebar for input
    with st.sidebar:
        st.header("Channel Analysis")
        channel_id = st.text_input("Enter YouTube Channel ID", help="Find this in your YouTube Studio under Advanced Settings")
        
        if st.button("Analyze Channel"):
            if not channel_id:
                st.warning("Please enter a Channel ID")
            else:
                with st.spinner("Fetching channel data..."):
                    channel_data = get_channel_analytics(channel_id)
                    if channel_data:
                        st.session_state.channel_data = channel_data
                        st.success("Data loaded successfully!")
    
    if "channel_data" in st.session_state:
        channel_data = st.session_state.channel_data
        basic_info = channel_data["basic_info"]
        videos_df = pd.DataFrame(channel_data["videos"])
        
        # Convert published_at to datetime
        videos_df["published_at"] = pd.to_datetime(videos_df["published_at"])
        videos_df["published_date"] = videos_df["published_at"].dt.date
        videos_df["duration_sec"] = videos_df["duration"].apply(parse_duration)
        
        # Calculate additional metrics
        videos_df["views_per_day"] = videos_df["views"] / ((pd.to_datetime("now") - videos_df["published_at"]).dt.days + 1)
        videos_df["like_ratio"] = videos_df["likes"] / videos_df["views"]
        
        # Header section with channel info
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(basic_info["thumbnail"], width=150)
            if basic_info["banner"]:
                st.image(basic_info["banner"], use_column_width=True)
        
        with col2:
            st.markdown(f"<h1 style='color:{COLOR_PALETTE['primary']}'>{basic_info['title']}</h1>", unsafe_allow_html=True)
            
            # Key metrics in columns
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.metric("Subscribers", format_number(basic_info["subscribers"]), help="Total channel subscribers")
            
            with m2:
                st.metric("Total Views", format_number(basic_info["total_views"]), help="Total views across all videos")
            
            with m3:
                st.metric("Total Videos", basic_info["total_videos"], help="Total videos uploaded")
            
            with m4:
                country = basic_info["country"] if basic_info["country"] != "N/A" else "US"
                estimated_earnings = calculate_earnings(basic_info["total_views"], country)
                st.metric("Estimated Earnings", f"${estimated_earnings:,.2f}", help="Estimated total earnings based on average RPM")
            
            st.caption(f"Channel created on {pd.to_datetime(basic_info['published_at']).strftime('%B %d, %Y')} • Country: {basic_info['country']}")
        
        st.markdown("---")
        
        # Earnings and conversions section
        st.subheader("💰 Earnings Insights")
        ecol1, ecol2, ecol3 = st.columns(3)
        
        with ecol1:
            rpm = 3.00 if basic_info["country"] == "US" else 1.50
            st.plotly_chart(
                px.bar(
                    x=["Estimated Earnings"],
                    y=[calculate_earnings(basic_info["total_views"], basic_info["country"])],
                    title="Total Estimated Earnings (USD)",
                    color_discrete_sequence=[COLOR_PALETTE['primary']],
                    labels={"y": "Amount", "x": ""}
                ).update_layout(
                    plot_bgcolor=COLOR_PALETTE['card'],
                    paper_bgcolor=COLOR_PALETTE['card'],
                    font_color=COLOR_PALETTE['text']
                ),
                use_container_width=True
            )
        
        with ecol2:
            monthly_earnings = calculate_earnings(basic_info["total_views"], basic_info["country"]) / max(1, (pd.to_datetime("now") - pd.to_datetime(basic_info["published_at"])).days / 30)
            st.plotly_chart(
                px.bar(
                    x=["Monthly Average"],
                    y=[monthly_earnings],
                    title="Monthly Average Earnings (USD)",
                    color_discrete_sequence=[COLOR_PALETTE['accent']],
                    labels={"y": "Amount", "x": ""}
                ).update_layout(
                    plot_bgcolor=COLOR_PALETTE['card'],
                    paper_bgcolor=COLOR_PALETTE['card'],
                    font_color=COLOR_PALETTE['text']
                ),
                use_container_width=True
            )
        
        with ecol3:
            prizes = convert_to_prizes(calculate_earnings(basic_info["total_views"], basic_info["country"]))
            st.markdown("**What your earnings could buy:**")
            for prize in prizes[:3]:  # Show top 3
                st.markdown(f"- {prize}")
        
        st.markdown("---")
        
        # Performance metrics section
        st.subheader("📈 Performance Metrics")
        
        # Time period filter
        time_filter = st.selectbox("Filter by time period:", 
                                 ["All time", "Last year", "Last 6 months", "Last 3 months", "Last month"])
        
        if time_filter != "All time":
            if time_filter == "Last year":
                cutoff = pd.to_datetime("now") - pd.DateOffset(years=1)
            elif time_filter == "Last 6 months":
                cutoff = pd.to_datetime("now") - pd.DateOffset(months=6)
            elif time_filter == "Last 3 months":
                cutoff = pd.to_datetime("now") - pd.DateOffset(months=3)
            else:  # Last month
                cutoff = pd.to_datetime("now") - pd.DateOffset(months=1)
            
            filtered_df = videos_df[videos_df["published_at"] >= cutoff]
        else:
            filtered_df = videos_df.copy()
        
        # Top metrics row
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            total_views = filtered_df["views"].sum()
            st.metric(f"Total Views ({time_filter})", format_number(total_views))
        
        with m2:
            avg_views = filtered_df["views"].mean()
            st.metric(f"Avg Views/Video", format_number(avg_views))
        
        with m3:
            total_likes = filtered_df["likes"].sum()
            st.metric(f"Total Likes", format_number(total_likes))
        
        with m4:
            engagement_rate = filtered_df["engagement"].mean()
            st.metric("Avg Engagement Rate", f"{engagement_rate:.2f}%")
        
        # Main charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Views over time
            views_over_time = filtered_df.groupby("published_date")["views"].sum().reset_index()
            fig = px.line(
                views_over_time, 
                x="published_date", 
                y="views",
                title=f"Views Over Time ({time_filter})",
                labels={"published_date": "Date", "views": "Views"},
                color_discrete_sequence=[COLOR_PALETTE['primary']]
            )
            fig.update_layout(
                plot_bgcolor=COLOR_PALETTE['card'],
                paper_bgcolor=COLOR_PALETTE['card'],
                font_color=COLOR_PALETTE['text'],
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Engagement scatter plot
            fig = px.scatter(
                filtered_df,
                x="views",
                y="engagement",
                size="likes",
                color="like_ratio",
                hover_name="title",
                title="Engagement vs Views",
                labels={"views": "Views", "engagement": "Engagement Rate (%)", "like_ratio": "Like/View Ratio"},
                color_continuous_scale=[COLOR_PALETTE['secondary'], COLOR_PALETTE['primary']]
            )
            fig.update_layout(
                plot_bgcolor=COLOR_PALETTE['card'],
                paper_bgcolor=COLOR_PALETTE['card'],
                font_color=COLOR_PALETTE['text']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Second charts row
        col3, col4 = st.columns(2)
        
        with col3:
            # Top performing videos
            top_videos = filtered_df.nlargest(10, "views")[["title", "views", "likes", "comments", "engagement"]]
            fig = px.bar(
                top_videos,
                x="views",
                y="title",
                orientation='h',
                title="Top Performing Videos by Views",
                labels={"views": "Views", "title": "Video Title"},
                color="engagement",
                color_continuous_scale=[COLOR_PALETTE['secondary'], COLOR_PALETTE['primary']]
            )
            fig.update_layout(
                plot_bgcolor=COLOR_PALETTE['card'],
                paper_bgcolor=COLOR_PALETTE['card'],
                font_color=COLOR_PALETTE['text'],
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col4:
            # Video duration analysis
            fig = px.scatter(
                filtered_df,
                x="duration_sec",
                y="views",
                size="likes",
                color="engagement",
                hover_name="title",
                title="Video Duration vs Performance",
                labels={"duration_sec": "Duration (seconds)", "views": "Views", "engagement": "Engagement Rate (%)"},
                color_continuous_scale=[COLOR_PALETTE['secondary'], COLOR_PALETTE['primary']]
            )
            fig.update_layout(
                plot_bgcolor=COLOR_PALETTE['card'],
                paper_bgcolor=COLOR_PALETTE['card'],
                font_color=COLOR_PALETTE['text']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Video details table
        st.subheader("🎬 Video Details")
        
        # Add filters for the table
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_views = st.number_input("Minimum Views", min_value=0, value=0, step=1000)
        
        with col2:
            min_likes = st.number_input("Minimum Likes", min_value=0, value=0, step=100)
        
        with col3:
            sort_by = st.selectbox("Sort By", ["Views", "Likes", "Comments", "Engagement", "Published Date"])
        
        # Apply filters
        filtered_table = filtered_df[
            (filtered_df["views"] >= min_views) & 
            (filtered_df["likes"] >= min_likes)
        ]
        
        # Sort data
        if sort_by == "Views":
            filtered_table = filtered_table.sort_values("views", ascending=False)
        elif sort_by == "Likes":
            filtered_table = filtered_table.sort_values("likes", ascending=False)
        elif sort_by == "Comments":
            filtered_table = filtered_table.sort_values("comments", ascending=False)
        elif sort_by == "Engagement":
            filtered_table = filtered_table.sort_values("engagement", ascending=False)
        else:
            filtered_table = filtered_table.sort_values("published_at", ascending=False)
        
        # Display table with thumbnails
        filtered_table["thumbnail_html"] = filtered_table["thumbnail"].apply(
            lambda x: f'<img src="{x}" width="120">')
        
        # Format numbers for display
        filtered_table["views_fmt"] = filtered_table["views"].apply(format_number)
        filtered_table["likes_fmt"] = filtered_table["likes"].apply(format_number)
        filtered_table["comments_fmt"] = filtered_table["comments"].apply(format_number)
        
        # Display the table
        st.write(
            filtered_table[["thumbnail_html", "title", "views_fmt", "likes_fmt", "comments_fmt", "engagement", "published_date"]].rename(columns={
                "thumbnail_html": "Thumbnail",
                "title": "Title",
                "views_fmt": "Views",
                "likes_fmt": "Likes",
                "comments_fmt": "Comments",
                "engagement": "Engagement (%)",
                "published_date": "Published Date"
            }).to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Channel growth projections
        st.subheader("📊 Growth Projections")
        
        # Calculate monthly growth
        monthly_uploads = videos_df.set_index("published_at").resample('M').size()
        monthly_views = videos_df.set_index("published_at").resample('M')["views"].sum()
        
        # Projection based on last 6 months
        if len(monthly_uploads) >= 6:
            avg_monthly_uploads = monthly_uploads[-6:].mean()
            avg_monthly_views = monthly_views[-6:].mean()
            
            projection_months = 12
            projected_uploads = [basic_info["total_videos"] + avg_monthly_uploads * i for i in range(1, projection_months+1)]
            projected_views = [basic_info["total_views"] + avg_monthly_views * i for i in range(1, projection_months+1)]
            
            projection_dates = pd.date_range(start=pd.to_datetime("now"), periods=projection_months+1, freq='M')
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly_uploads.index,
                    y=monthly_uploads,
                    name="Actual Uploads",
                    line=dict(color=COLOR_PALETTE['primary'], width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=projection_dates,
                    y=[monthly_uploads[-1]] + projected_uploads,
                    name="Projected Uploads",
                    line=dict(color=COLOR_PALETTE['primary'], width=3, dash='dot')
                ))
                fig.update_layout(
                    title="Monthly Uploads & Projection",
                    xaxis_title="Date",
                    yaxis_title="Videos Uploaded",
                    plot_bgcolor=COLOR_PALETTE['card'],
                    paper_bgcolor=COLOR_PALETTE['card'],
                    font_color=COLOR_PALETTE['text'],
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly_views.index,
                    y=monthly_views,
                    name="Actual Views",
                    line=dict(color=COLOR_PALETTE['accent'], width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=projection_dates,
                    y=[monthly_views[-1]] + projected_views,
                    name="Projected Views",
                    line=dict(color=COLOR_PALETTE['accent'], width=3, dash='dot')
                ))
                fig.update_layout(
                    title="Monthly Views & Projection",
                    xaxis_title="Date",
                    yaxis_title="Views",
                    plot_bgcolor=COLOR_PALETTE['card'],
                    paper_bgcolor=COLOR_PALETTE['card'],
                    font_color=COLOR_PALETTE['text'],
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Projected earnings
            projected_earnings = calculate_earnings(projected_views[-1], basic_info["country"])
            current_earnings = calculate_earnings(basic_info["total_views"], basic_info["country"])
            
            st.metric(
                "Projected Annual Earnings Growth",
                f"${projected_earnings:,.2f}",
                delta=f"${projected_earnings - current_earnings:,.2f}",
                delta_color="normal",
                help="Based on last 6 months average performance"
            )

if __name__ == "__main__":
    main()
