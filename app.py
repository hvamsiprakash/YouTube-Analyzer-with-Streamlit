# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.cluster import KMeans

# Download NLTK data
nltk.download('vader_lexicon')

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=st.secrets["YOUTUBE_API_KEY"])

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for dark theme with enhanced styling
def set_dark_theme():
    st.markdown("""
    <style>
    :root {
        --primary-color: #FF4B4B;
        --secondary-color: #0E1117;
        --text-color: #FFFFFF;
        --card-bg: #1A1D24;
        --dark-red: #CC0000;
        --light-red: #FF6B6B;
        --accent-red: #FF3333;
    }
    
    .main {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
        border-bottom: 1px solid var(--dark-red);
        padding-bottom: 8px;
    }
    
    .metric-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .insight-card {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    
    .insight-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(255, 75, 75, 0.2);
    }
    
    .insight-title {
        color: var(--light-red);
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
    }
    
    .insight-value {
        color: var(--text-color);
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    
    .insight-description {
        color: #AAAAAA;
        font-size: 13px;
        line-height: 1.4;
    }
    
    .stSelectbox, .stSlider, .stDateInput, .stTextInput {
        background-color: var(--card-bg) !important;
        border-color: #333 !important;
        color: white !important;
    }
    
    .st-bb {
        background-color: var(--card-bg) !important;
    }
    
    .stDataFrame {
        background-color: var(--card-bg) !important;
    }
    
    .filter-container {
        background-color: var(--card-bg);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    
    .filter-title {
        color: var(--light-red);
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .plotly-chart {
        border-radius: 10px;
        border: 1px solid #333;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-color);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-red);
    }
    
    /* Custom tooltips */
    .stTooltip {
        background-color: var(--card-bg) !important;
        border: 1px solid var(--primary-color) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

set_dark_theme()

# Function to get comprehensive channel analytics with error handling
@st.cache_data(ttl=3600, show_spinner="Fetching channel data...")
def get_channel_analytics(channel_id):
    try:
        # Get channel statistics
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails,contentDetails",
            id=channel_id
        ).execute()
        
        if not channel_response.get("items"):
            st.error("❌ Channel not found. Please check the Channel ID.")
            return None
            
        channel_info = channel_response["items"][0]
        
        # Get channel videos (limited to 500 for performance)
        videos = []
        next_page_token = None
        
        for _ in range(10):  # Max 10 pages (500 videos)
            videos_response = youtube.search().list(
                channelId=channel_id,
                type="video",
                part="id,snippet",
                maxResults=50,
                order="date",
                pageToken=next_page_token
            ).execute()
            
            video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]
            
            # Get detailed video statistics in batches
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                video_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails",
                    id=",".join(batch_ids)
                ).execute()
                
                for video in video_response.get("items", []):
                    stats = video["statistics"]
                    snippet = video["snippet"]
                    details = video["contentDetails"]
                    
                    videos.append({
                        "title": snippet.get("title", "N/A"),
                        "video_id": video["id"],
                        "published_at": snippet.get("publishedAt", "N/A"),
                        "duration": details.get("duration", "PT0M"),
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "category_id": snippet.get("categoryId", ""),
                        "description": snippet.get("description", "")
                    })
            
            next_page_token = videos_response.get("nextPageToken")
            if not next_page_token:
                break
        
        # Calculate engagement metrics
        for video in videos:
            video["engagement"] = ((video["likes"] + video["comments"]) / max(1, video["views"])) * 100
        
        # Get channel playlists
        playlists = []
        next_page_token = None
        
        for _ in range(5):  # Max 5 pages (250 playlists)
            playlists_response = youtube.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for playlist in playlists_response.get("items", []):
                playlists.append({
                    "title": playlist["snippet"]["title"],
                    "playlist_id": playlist["id"],
                    "item_count": playlist["contentDetails"]["itemCount"],
                    "thumbnail": playlist["snippet"]["thumbnails"]["high"]["url"]
                })
            
            next_page_token = playlists_response.get("nextPageToken")
            if not next_page_token:
                break
        
        # Format the data
        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "custom_url": channel_info["snippet"].get("customUrl", "N/A"),
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country", "N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"],
                "banner": channel_info["brandingSettings"].get("image", {}).get("bannerExternalUrl", "N/A"),
                "topics": channel_info.get("topicDetails", {}).get("topicCategories", []),
                "uploads_playlist": channel_info["contentDetails"]["relatedPlaylists"]["uploads"]
            },
            "statistics": {
                "view_count": int(channel_info["statistics"]["viewCount"]),
                "subscriber_count": int(channel_info["statistics"]["subscriberCount"]),
                "video_count": int(channel_info["statistics"]["videoCount"]),
                "hidden_subscriber_count": channel_info["statistics"]["hiddenSubscriberCount"]
            },
            "videos": sorted(videos, key=lambda x: x["views"], reverse=True),
            "playlists": playlists
        }
        
        return channel_data
        
    except Exception as e:
        st.error(f"❌ Error fetching channel data: {str(e)}")
        return None

# Function to analyze video titles and descriptions
def analyze_content(videos):
    titles = [video['title'] for video in videos]
    descriptions = [video['description'] for video in videos]
    
    # Sentiment analysis
    sia = SentimentIntensityAnalyzer()
    title_sentiments = [sia.polarity_scores(title)['compound'] for title in titles]
    avg_sentiment = np.mean(title_sentiments) if title_sentiments else 0
    
    # Word cloud analysis
    wordcloud_text = ' '.join(titles + descriptions)
    
    # Keyword extraction
    blob = TextBlob(wordcloud_text)
    nouns = [word for word, tag in blob.tags if tag == 'NN']
    top_keywords = pd.Series(nouns).value_counts().head(5).index.tolist()
    
    return {
        'avg_sentiment': avg_sentiment,
        'top_keywords': top_keywords,
        'wordcloud_text': wordcloud_text
    }

# Function to cluster videos by performance
def cluster_videos(videos_df):
    try:
        # Prepare features for clustering
        X = videos_df[['views', 'likes', 'comments', 'engagement']]
        X = (X - X.mean()) / X.std()  # Standardize
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        videos_df['cluster'] = kmeans.fit_predict(X)
        
        # Analyze clusters
        cluster_stats = videos_df.groupby('cluster')[['views', 'likes', 'comments', 'engagement']].mean()
        
        return videos_df, cluster_stats
    except:
        return videos_df, None

# Function to format numbers
def format_number(num):
    if num >= 1000000000:
        return f"{num/1000000000:.1f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

# Function to parse ISO 8601 duration
def parse_duration(duration):
    try:
        if duration.startswith('PT'):
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
        return 0
    except:
        return 0

# Function to format seconds to HH:MM:SS
def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

# Function to create a time series heatmap
def create_time_heatmap(df, date_col, value_col, title):
    df['date'] = pd.to_datetime(df[date_col])
    df['day_of_week'] = df['date'].dt.day_name()
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    
    heatmap_df = df.groupby(['year', 'week_of_year', 'day_of_week'])[value_col].sum().reset_index()
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_df['day_of_week'] = pd.Categorical(heatmap_df['day_of_week'], categories=days_order, ordered=True)
    
    fig = px.density_heatmap(
        heatmap_df,
        x='day_of_week',
        y='week_of_year',
        z=value_col,
        facet_col='year',
        title=title,
        color_continuous_scale='reds',
        height=400
    )
    
    fig.update_layout(
        plot_bgcolor="#1A1D24",
        paper_bgcolor="#0E1117",
        font={"color": "white"},
        hovermode="closest"
    )
    
    return fig

# Main dashboard function - First Half
def youtube_dashboard_first_half():
    st.title("🎬 YouTube Pro Analytics Dashboard")
    
    # Channel ID input at top
    col1, col2 = st.columns([3, 1])
    with col1:
        channel_id = st.text_input("Enter YouTube Channel ID", key="channel_id", 
                                 placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    with col2:
        st.markdown("")
        st.markdown("")
        analyze_btn = st.button("🚀 Analyze Channel", key="analyze_btn")
    
    if analyze_btn and not channel_id:
        st.error("Please enter a valid YouTube Channel ID")
        st.stop()
    
    if analyze_btn and channel_id:
        with st.spinner("Fetching and analyzing channel data..."):
            channel_data = get_channel_analytics(channel_id)
            
        if not channel_data:
            st.stop()
            
        # Filters container
        with st.expander("⚙️ Dashboard Filters", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                time_range = st.selectbox(
                    "Time Range", 
                    ["Last 30 days", "Last 90 days", "Last 6 months", 
                     "Last year", "Last 2 years", "All time"],
                    key="time_range"
                )
                
            with col2:
                currency = st.selectbox(
                    "Currency", 
                    ["USD", "INR", "EUR"],
                    key="currency"
                )
                
            with col3:
                cpm_range = st.selectbox(
                    "CPM Range", 
                    ["low", "medium", "high"],
                    format_func=lambda x: {"low": "Low", "medium": "Medium", "high": "High"}[x],
                    key="cpm_range"
                )
        
        # Calculate time range filter
        now = datetime.now()
        if time_range == "Last 30 days":
            cutoff_date = now - timedelta(days=30)
        elif time_range == "Last 90 days":
            cutoff_date = now - timedelta(days=90)
        elif time_range == "Last 6 months":
            cutoff_date = now - relativedelta(months=6)
        elif time_range == "Last year":
            cutoff_date = now - relativedelta(years=1)
        elif time_range == "Last 2 years":
            cutoff_date = now - relativedelta(years=2)
        else:  # All time
            cutoff_date = datetime.min
            
        # Filter videos by time range
        filtered_videos = []
        for video in channel_data["videos"]:
            try:
                pub_date = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ")
                if pub_date >= cutoff_date:
                    filtered_videos.append(video)
            except:
                continue
        
        # Create DataFrame for filtered videos
        video_df = pd.DataFrame(filtered_videos)
        video_df["published_at"] = pd.to_datetime(video_df["published_at"])
        video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
        video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
        video_df["engagement"] = video_df["engagement"].round(2)
        video_df["publish_day"] = video_df["published_at"].dt.day_name()
        video_df["publish_hour"] = video_df["published_at"].dt.hour
        video_df["publish_month"] = video_df["published_at"].dt.strftime("%Y-%m")
        
        # Content analysis
        content_analysis = analyze_content(filtered_videos)
        
        # Cluster videos by performance
        video_df, cluster_stats = cluster_videos(video_df)
        
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
            if channel_data["basic_info"]["topics"]:
                st.markdown("**Topics:** " + ", ".join([topic.split('/')[-1].replace('_', ' ') for topic in channel_data["basic_info"]["topics"][:3]]))
        
        st.markdown("---")
        
        # Key Metrics
        st.subheader("📊 Channel Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">👥 Subscribers</div>
                <div class="insight-value">{format_number(channel_data['statistics']['subscriber_count'])}</div>
                <div class="insight-description">
                    {'' if channel_data['statistics']['hidden_subscriber_count'] else 'Public subscriber count'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">👀 Total Views</div>
                <div class="insight-value">{format_number(channel_data['statistics']['view_count'])}</div>
                <div class="insight-description">
                    {len(filtered_videos)} videos in selected period
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">🎬 Total Videos</div>
                <div class="insight-value">{format_number(channel_data['statistics']['video_count'])}</div>
                <div class="insight-description">
                    {len(filtered_videos)} in selected period
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            est_earnings = (channel_data['statistics']['view_count'] / 1000) * 3  # Medium CPM estimate
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">💰 Estimated Earnings</div>
                <div class="insight-value">${format_number(est_earnings)}</div>
                <div class="insight-description">
                    Based on medium CPM ($3 per 1000 views)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # First 15 Insights in a 3x5 grid
        st.subheader("🔍 Channel Insights")
        
        # Row 1
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Insight 1: Best Performing Video
            top_video = video_df.iloc[0] if not video_df.empty else None
            if top_video is not None:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🎯 Best Performing Video</div>
                    <div class="insight-value">{format_number(top_video['views'])} views</div>
                    <div class="insight-description">
                        "{top_video['title'][:50]}{'...' if len(top_video['title']) > 50 else ''}"
                        <br>Engagement: {top_video['engagement']:.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Insight 2: Average Engagement Rate
            avg_engagement = video_df['engagement'].mean() if not video_df.empty else 0
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">💬 Avg Engagement Rate</div>
                <div class="insight-value">{avg_engagement:.2f}%</div>
                <div class="insight-description">
                    (Likes + Comments) / Views * 100
                    <br>Higher than 5% is considered good
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Insight 3: Optimal Video Length
            if not video_df.empty:
                video_df['duration_min'] = video_df['duration_sec'] / 60
                bins = [0, 5, 10, 15, 20, 30, 60, float('inf')]
                labels = ['<5m', '5-10m', '10-15m', '15-20m', '20-30m', '30-60m', '60m+']
                video_df['duration_bin'] = pd.cut(video_df['duration_min'], bins=bins, labels=labels)
                
                optimal_bin = video_df.groupby('duration_bin')['views'].mean().idxmax()
                optimal_range = str(optimal_bin)
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">⏱️ Optimal Video Length</div>
                    <div class="insight-value">{optimal_range}</div>
                    <div class="insight-description">
                        Videos in this duration range have the highest average views
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Row 2
        col4, col5, col6 = st.columns(3)
        
        with col4:
            # Insight 4: Best Day to Publish
            if not video_df.empty:
                best_day = video_df.groupby('publish_day')['views'].mean().idxmax()
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📅 Best Day to Publish</div>
                    <div class="insight-value">{best_day}</div>
                    <div class="insight-description">
                        Videos published on this day historically get more views
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col5:
            # Insight 5: Best Hour to Publish
            if not video_df.empty:
                best_hour = video_df.groupby('publish_hour')['views'].mean().idxmax()
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">⏰ Best Hour to Publish</div>
                    <div class="insight-value">{best_hour}:00 - {best_hour+1}:00</div>
                    <div class="insight-description">
                        Optimal time slot for maximum views
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col6:
            # Insight 6: Content Sentiment
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">😊 Content Sentiment</div>
                <div class="insight-value">{'Positive' if content_analysis['avg_sentiment'] > 0.05 else 'Neutral' if content_analysis['avg_sentiment'] > -0.05 else 'Negative'}</div>
                <div class="insight-description">
                    Average sentiment score: {content_analysis['avg_sentiment']:.2f}
                    <br>(Range: -1 to 1)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Row 3
        col7, col8, col9 = st.columns(3)
        
        with col7:
            # Insight 7: Top Keywords
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">🔑 Top Keywords</div>
                <div class="insight-value">{', '.join(content_analysis['top_keywords'][:3])}</div>
                <div class="insight-description">
                    Most frequently used nouns in video titles/descriptions
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col8:
            # Insight 8: Content Consistency
            if len(video_df) > 1:
                video_df['days_between'] = video_df['published_at'].diff().dt.days
                avg_days_between = video_df['days_between'].mean()
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">⏳ Publishing Frequency</div>
                    <div class="insight-value">{avg_days_between:.1f} days</div>
                    <div class="insight-description">
                        Average time between video uploads
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col9:
            # Insight 9: Like-to-View Ratio
            if not video_df.empty:
                avg_like_ratio = (video_df['likes'].sum() / video_df['views'].sum()) * 100
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">👍 Like-to-View Ratio</div>
                    <div class="insight-value">{avg_like_ratio:.2f}%</div>
                    <div class="insight-description">
                        Higher ratio indicates more engaging content
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Row 4
        col10, col11, col12 = st.columns(3)
        
        with col10:
            # Insight 10: Comment Engagement
            if not video_df.empty:
                avg_comment_ratio = (video_df['comments'].sum() / video_df['views'].sum()) * 100
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">💬 Comment Engagement</div>
                    <div class="insight-value">{avg_comment_ratio:.2f}%</div>
                    <div class="insight-description">
                        % of viewers who leave comments
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col11:
            # Insight 11: View Velocity
            if not video_df.empty:
                latest_videos = video_df.sort_values('published_at', ascending=False).head(5)
                avg_velocity = latest_videos['views'].mean() / (now - latest_videos['published_at'].min()).days
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🚀 View Velocity</div>
                    <div class="insight-value">{format_number(avg_velocity)}/day</div>
                    <div class="insight-description">
                        Average daily views for latest 5 videos
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col12:
            # Insight 12: Content Clusters
            if cluster_stats is not None:
                best_cluster = cluster_stats['views'].idxmax()
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📊 Performance Clusters</div>
                    <div class="insight-value">Cluster {best_cluster+1}</div>
                    <div class="insight-description">
                        Your best-performing content cluster
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Row 5
        col13, col14, col15 = st.columns(3)
        
        with col13:
            # Insight 13: Audience Retention
            if not video_df.empty:
                retention_rate = (video_df['views'].sum() / channel_data['statistics']['view_count']) * 100
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">👥 Audience Retention</div>
                    <div class="insight-value">{retention_rate:.1f}%</div>
                    <div class="insight-description">
                        % of total channel views from selected period
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col14:
            # Insight 14: Playlist Performance
            if channel_data['playlists']:
                avg_playlist_items = sum(p['item_count'] for p in channel_data['playlists']) / len(channel_data['playlists'])
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📚 Playlist Stats</div>
                    <div class="insight-value">{len(channel_data['playlists'])} playlists</div>
                    <div class="insight-description">
                        Avg {avg_playlist_items:.1f} videos per playlist
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col15:
            # Insight 15: Content Diversity
            if not video_df.empty:
                unique_categories = video_df['category_id'].nunique()
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">🌈 Content Diversity</div>
                    <div class="insight-value">{unique_categories} categories</div>
                    <div class="insight-description">
                        Number of different video categories
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance Charts Section
        st.subheader("📈 Performance Analytics")
        
        # Row 1: Views and Engagement
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Filter container for views chart
            with st.container():
                st.markdown('<div class="filter-title">Views Over Time</div>', unsafe_allow_html=True)
                min_views = st.slider(
                    "Minimum Views", 
                    min_value=0, 
                    max_value=int(video_df["views"].max()), 
                    value=0,
                    step=1000,
                    key="min_views"
                )
                
                filtered_chart_df = video_df[video_df["views"] >= min_views]
                
                # Views over time with trendline
                fig_views = px.scatter(
                    filtered_chart_df, 
                    x="published_at", 
                    y="views",
                    trendline="lowess",
                    trendline_color_override="#FF4B4B",
                    title="Video Views Over Time with Trend",
                    color_discrete_sequence=["#FF4B4B"],
                    labels={"published_at": "Publish Date", "views": "Views"},
                    hover_name="title",
                    hover_data=["engagement", "duration_formatted"]
                )
                fig_views.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    hovermode="closest",
                    height=400
                )
                st.plotly_chart(fig_views, use_container_width=True)
            
        with col_chart2:
            # Filter container for engagement chart
            with st.container():
                st.markdown('<div class="filter-title">Engagement Analysis</div>', unsafe_allow_html=True)
                min_duration = st.slider(
                    "Minimum Duration (min)", 
                    min_value=0, 
                    max_value=int(video_df["duration_sec"].max() // 60), 
                    value=0,
                    step=1,
                    key="min_duration"
                )
                
                filtered_eng_df = video_df[video_df["duration_sec"] >= min_duration * 60]
                
                # Engagement vs Duration bubble chart
                fig_engagement = px.scatter(
                    filtered_eng_df,
                    x="duration_sec",
                    y="engagement",
                    size="views",
                    color="views",
                    title="Engagement Rate vs Video Duration",
                    color_continuous_scale="reds",
                    labels={
                        "duration_sec": "Duration (seconds)",
                        "engagement": "Engagement Rate (%)",
                        "views": "Views"
                    },
                    hover_name="title",
                    hover_data=["published_at"]
                )
                
                # Add optimal duration line
                if not filtered_eng_df.empty:
                    optimal_duration = filtered_eng_df.groupby(pd.cut(filtered_eng_df["duration_sec"], bins=10))["engagement"].mean().idxmax().mid
                    fig_engagement.add_vline(
                        x=optimal_duration, 
                        line_dash="dash", 
                        line_color="white",
                        annotation_text=f"Optimal: ~{optimal_duration//60}m",
                        annotation_position="top right"
                    )
                
                fig_engagement.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    hovermode="closest",
                    height=400
                )
                st.plotly_chart(fig_engagement, use_container_width=True)

# Run the first half of the dashboard
if __name__ == "__main__":
    youtube_dashboard_first_half()
