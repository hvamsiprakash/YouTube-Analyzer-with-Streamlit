# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
from streamlit.components.v1 import html

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for dark theme with red accents
def set_dark_theme():
    st.markdown("""
    <style>
    :root {
        --primary-color: #FF0000;
        --secondary-color: #0E1117;
        --text-color: #FFFFFF;
        --card-bg: #1A1D24;
        --dark-red: #8B0000;
        --medium-red: #CC0000;
        --light-red: #FF3333;
    }
    
    .main {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }
    
    .st-bw, .st-at, .st-cn {
        background-color: var(--secondary-color) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
    }
    
    .metric-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border-left: 4px solid var(--primary-color);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(255, 0, 0, 0.3);
    }
    
    .metric-title {
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    
    .metric-value {
        color: var(--text-color);
        font-size: 28px;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .metric-change {
        font-size: 12px;
        display: flex;
        align-items: center;
    }
    
    .positive {
        color: #00FF00;
    }
    
    .negative {
        color: #FF0000;
    }
    
    .neutral {
        color: #AAAAAA;
    }
    
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin: 20px 0;
    }
    
    .insight-card {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border-left: 4px solid var(--primary-color);
        transition: transform 0.3s ease;
        height: 100%;
    }
    
    .insight-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(255, 0, 0, 0.3);
    }
    
    .insight-title {
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    
    .insight-value {
        color: var(--text-color);
        font-size: 28px;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .insight-description {
        color: #AAAAAA;
        font-size: 12px;
        line-height: 1.4;
    }
    
    .chart-container {
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .chart-title {
        color: var(--text-color);
        font-size: 18px;
        font-weight: 700;
    }
    
    .chart-filters {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .filter-label {
        color: #AAAAAA;
        font-size: 12px;
        margin-right: 5px;
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
    
    .css-1aumxhk {
        background-color: var(--secondary-color) !important;
    }
    
    .css-1v0mbdj {
        border: 1px solid #333 !important;
    }
    
    .tab-content {
        padding: 15px 0;
    }
    
    .section-divider {
        border-top: 2px solid var(--medium-red);
        margin: 20px 0;
        opacity: 0.5;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--card-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--medium-red);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color);
    }
    
    /* Hide Streamlit footer and hamburger menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

set_dark_theme()

# Function to get comprehensive channel analytics with error handling
@st.cache_data(ttl=3600, show_spinner="Fetching channel data...")
def get_channel_analytics(channel_id):
    try:
        # Get channel statistics
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails",
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
                        "category_id": snippet.get("categoryId", "")
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
                "topics": channel_info.get("topicDetails", {}).get("topicCategories", [])
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

# Function to calculate estimated earnings with more sophisticated model
def calculate_earnings(videos_data, currency="USD", cpm_range="medium"):
    # RPM (Revenue Per Mille) estimates by category and region
    rpm_rates = {
        "USD": {
            "low": {"US": 1.0, "IN": 0.5, "other": 0.8},
            "medium": {"US": 3.0, "IN": 1.5, "other": 2.0},
            "high": {"US": 5.0, "IN": 2.5, "other": 3.5}
        },
        "INR": {
            "low": {"US": 80, "IN": 40, "other": 60},
            "medium": {"US": 240, "IN": 120, "other": 160},
            "high": {"US": 400, "IN": 200, "other": 280}
        },
        "EUR": {
            "low": {"US": 0.9, "IN": 0.45, "other": 0.7},
            "medium": {"US": 2.7, "IN": 1.35, "other": 1.8},
            "high": {"US": 4.5, "IN": 2.25, "other": 3.15}
        }
    }
    
    # Calculate total views and views by month
    total_views = sum(video["views"] for video in videos_data)
    
    monthly_data = {}
    for video in videos_data:
        try:
            month = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {
                    "views": 0,
                    "videos": 0,
                    "estimated_earnings": 0
                }
            monthly_data[month]["views"] += video["views"]
            monthly_data[month]["videos"] += 1
        except:
            continue
    
    # Calculate earnings by month with different RPM for different regions
    for month in monthly_data:
        # Simplified - assuming 60% US views, 10% India, 30% other for premium channels
        us_views = monthly_data[month]["views"] * 0.6
        in_views = monthly_data[month]["views"] * 0.1
        other_views = monthly_data[month]["views"] * 0.3
        
        us_earnings = (us_views / 1000) * rpm_rates[currency][cpm_range]["US"]
        in_earnings = (in_views / 1000) * rpm_rates[currency][cpm_range]["IN"]
        other_earnings = (other_views / 1000) * rpm_rates[currency][cpm_range]["other"]
        
        monthly_data[month]["estimated_earnings"] = us_earnings + in_earnings + other_earnings
    
    total_earnings = sum(month["estimated_earnings"] for month in monthly_data.values())
    
    return {
        "total_earnings": total_earnings,
        "monthly_earnings": monthly_data,
        "currency": currency,
        "cpm_range": cpm_range,
        "total_views": total_views,
        "estimated_rpm": total_earnings / (total_views / 1000) if total_views > 0 else 0
    }

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

# Main dashboard function
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")
    
    # Channel input at top
    col_input1, col_input2, col_input3 = st.columns([3, 2, 1])
    
    with col_input1:
        channel_id = st.text_input("Enter YouTube Channel ID", 
                                 placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA",
                                 key="channel_input")
    
    with col_input2:
        time_range = st.selectbox(
            "Time Range",
            ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "Last 2 years", "All time"],
            key="time_range"
        )
    
    with col_input3:
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
        video_df["publish_month"] = video_df["published_at"].dt.strftime("%Y-%m")
        video_df["publish_hour"] = video_df["published_at"].dt.hour
        video_df["duration_min"] = video_df["duration_sec"] / 60
        
        # Create duration bins
        bins = [0, 5, 10, 15, 20, 30, 60, float('inf')]
        labels = ['<5m', '5-10m', '10-15m', '15-20m', '20-30m', '30-60m', '60m+']
        video_df['duration_bin'] = pd.cut(video_df['duration_min'], bins=bins, labels=labels)
        
        # Main dashboard layout
        st.markdown("---")
        
        # Channel header
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
        
        # Create 3x3 grid for metrics
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Subscribers</div>
                    <div class="metric-value">{format_number(channel_data['statistics']['subscriber_count'])}</div>
                    <div class="metric-change">
                        <span class="neutral">Hidden: {'Yes' if channel_data['statistics']['hidden_subscriber_count'] else 'No'}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Views</div>
                    <div class="metric-value">{format_number(channel_data['statistics']['view_count'])}</div>
                    <div class="metric-change">
                        <span class="neutral">{len(filtered_videos)} videos in selected period</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Videos</div>
                    <div class="metric-value">{format_number(channel_data['statistics']['video_count'])}</div>
                    <div class="metric-change">
                        <span class="neutral">{len(filtered_videos)} in selected period</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with st.container():
            col4, col5, col6 = st.columns(3)
            
            with col4:
                # Calculate earnings with default settings
                earnings_data = calculate_earnings(filtered_videos)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Estimated Earnings</div>
                    <div class="metric-value">${format_number(earnings_data['total_earnings'])}</div>
                    <div class="metric-change">
                        <span class="neutral">RPM: ${earnings_data['estimated_rpm']:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col5:
                avg_views = video_df["views"].mean() if not video_df.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Avg. Views/Video</div>
                    <div class="metric-value">{format_number(avg_views)}</div>
                    <div class="metric-change">
                        <span class="neutral">Last {len(filtered_videos)} videos</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col6:
                avg_engagement = video_df["engagement"].mean() if not video_df.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Avg. Engagement</div>
                    <div class="metric-value">{avg_engagement:.2f}%</div>
                    <div class="metric-change">
                        <span class="neutral">(Likes + Comments) / Views</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Top Insights Section
        st.subheader("🔍 Top Insights")
        
        # Create 3x3 grid for insights
        with st.container():
            col_insight1, col_insight2, col_insight3 = st.columns(3)
            
            with col_insight1:
                # Best Performing Video
                top_video = video_df.iloc[0] if not video_df.empty else None
                if top_video is not None:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">🎯 Best Performing Video</div>
                        <div class="metric-value">{format_number(top_video['views'])}</div>
                        <div class="metric-change">
                            <span class="neutral">"{top_video['title'][:30]}{'...' if len(top_video['title']) > 30 else ''}"</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_insight2:
                # Optimal Video Length
                if not video_df.empty:
                    optimal_bin = video_df.groupby('duration_bin')['views'].mean().idxmax()
                    optimal_range = str(optimal_bin)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">⏱️ Optimal Video Length</div>
                        <div class="metric-value">{optimal_range}</div>
                        <div class="metric-change">
                            <span class="neutral">Highest average views</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_insight3:
                # Best Day to Publish
                if not video_df.empty:
                    best_day = video_df.groupby('publish_day')['views'].mean().idxmax()
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">📅 Best Day to Publish</div>
                        <div class="metric-value">{best_day}</div>
                        <div class="metric-change">
                            <span class="neutral">Higher average views</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with st.container():
            col_insight4, col_insight5, col_insight6 = st.columns(3)
            
            with col_insight4:
                # RPM (Revenue Per Mille)
                rpm = earnings_data['estimated_rpm']
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💰 RPM (Revenue Per Mille)</div>
                    <div class="metric-value">${rpm:.2f}</div>
                    <div class="metric-change">
                        <span class="neutral">Earnings per 1,000 views</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_insight5:
                # Audience Retention
                if not video_df.empty:
                    retention_rate = (video_df['views'].sum() / channel_data['statistics']['view_count']) * 100
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">👥 Audience Retention</div>
                        <div class="metric-value">{retention_rate:.1f}%</div>
                        <div class="metric-change">
                            <span class="neutral">% of total channel views</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_insight6:
                # Publishing Frequency
                if len(video_df) > 1:
                    video_df['days_between'] = video_df['published_at'].diff().dt.days
                    avg_days_between = video_df['days_between'].mean()
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">⏳ Publishing Frequency</div>
                        <div class="metric-value">{avg_days_between:.1f} days</div>
                        <div class="metric-change">
                            <span class="neutral">Avg time between uploads</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance Charts Section - Using session state to maintain filter values
        st.subheader("📈 Performance Analytics")
        
        # Tab layout for different chart types
        tab1, tab2, tab3 = st.tabs(["Views Analysis", "Engagement Metrics", "Earnings & Growth"])
        
        with tab1:
            # Views Analysis Tab
            st.markdown("### Video Views Analysis")
            
            # Create a container for filters
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    min_views = st.slider(
                        "Minimum Views", 
                        min_value=0, 
                        max_value=int(video_df["views"].max()), 
                        value=0,
                        step=1000,
                        key="views_min_views"
                    )
                
                with col2:
                    duration_filter = st.selectbox(
                        "Duration Range",
                        ["All", "<5 min", "5-10 min", "10-15 min", "15-20 min", "20-30 min", "30+ min"],
                        key="views_duration_filter"
                    )
            
            # Apply filters
            filtered_views_df = video_df[video_df["views"] >= min_views]
            
            if duration_filter != "All":
                if duration_filter == "<5 min":
                    filtered_views_df = filtered_views_df[filtered_views_df["duration_min"] < 5]
                elif duration_filter == "5-10 min":
                    filtered_views_df = filtered_views_df[(filtered_views_df["duration_min"] >= 5) & (filtered_views_df["duration_min"] < 10)]
                elif duration_filter == "10-15 min":
                    filtered_views_df = filtered_views_df[(filtered_views_df["duration_min"] >= 10) & (filtered_views_df["duration_min"] < 15)]
                elif duration_filter == "15-20 min":
                    filtered_views_df = filtered_views_df[(filtered_views_df["duration_min"] >= 15) & (filtered_views_df["duration_min"] < 20)]
                elif duration_filter == "20-30 min":
                    filtered_views_df = filtered_views_df[(filtered_views_df["duration_min"] >= 20) & (filtered_views_df["duration_min"] < 30)]
                else:  # 30+ min
                    filtered_views_df = filtered_views_df[filtered_views_df["duration_min"] >= 30]
            
            # Row 1: Views over time and by duration
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Views over time with trendline
                if not filtered_views_df.empty:
                    fig_views = px.line(
                        filtered_views_df, 
                        x="published_at", 
                        y="views",
                        title="Video Views Over Time",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"published_at": "Publish Date", "views": "Views"},
                        hover_name="title",
                        hover_data=["engagement", "duration_formatted"]
                    )
                    
                    # Add trendline
                    fig_views.add_scatter(
                        x=filtered_views_df["published_at"],
                        y=filtered_views_df["views"].rolling(7, min_periods=1).mean(),
                        mode='lines',
                        name='7-Day Avg',
                        line=dict(color='white', width=2, dash='dash')
                    )
                    
                    fig_views.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400,
                        showlegend=True
                    )
                    st.plotly_chart(fig_views, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart2:
                # Views by duration
                if not filtered_views_df.empty:
                    duration_views = filtered_views_df.groupby('duration_bin')['views'].mean().reset_index()
                    
                    fig_duration = px.bar(
                        duration_views,
                        x="duration_bin",
                        y="views",
                        title="Average Views by Video Duration",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"duration_bin": "Duration Range", "views": "Average Views"}
                    )
                    
                    # Add optimal duration marker
                    optimal_duration = duration_views.loc[duration_views['views'].idxmax(), 'duration_bin']
                    fig_duration.add_vline(
                        x=optimal_duration,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Optimal: {optimal_duration}",
                        annotation_position="top right"
                    )
                    
                    fig_duration.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_duration, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
            
            # Row 2: Views by day of week and hour of day
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # Views by day of week
                if not filtered_views_df.empty:
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_views = filtered_views_df.groupby('publish_day')['views'].sum().reindex(day_order).reset_index()
                    
                    fig_day = px.bar(
                        day_views,
                        x="publish_day",
                        y="views",
                        title="Total Views by Day of Week",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"publish_day": "Day of Week", "views": "Total Views"}
                    )
                    
                    # Add best day marker
                    best_day = day_views.loc[day_views['views'].idxmax(), 'publish_day']
                    fig_day.add_vline(
                        x=best_day,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Best: {best_day}",
                        annotation_position="top right"
                    )
                    
                    fig_day.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400,
                        xaxis={'categoryorder': 'array', 'categoryarray': day_order}
                    )
                    st.plotly_chart(fig_day, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart4:
                # Views by hour of day
                if not filtered_views_df.empty:
                    hour_views = filtered_views_df.groupby('publish_hour')['views'].sum().reset_index()
                    
                    fig_hour = px.bar(
                        hour_views,
                        x="publish_hour",
                        y="views",
                        title="Total Views by Hour of Day",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"publish_hour": "Hour of Day (24h)", "views": "Total Views"}
                    )
                    
                    # Add best hour marker
                    best_hour = hour_views.loc[hour_views['views'].idxmax(), 'publish_hour']
                    fig_hour.add_vline(
                        x=best_hour,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Best: {best_hour}:00",
                        annotation_position="top right"
                    )
                    
                    fig_hour.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_hour, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
        
        with tab2:
            # Engagement Metrics Tab
            st.markdown("### Engagement Metrics Analysis")
            
            # Create a container for filters
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    min_engagement = st.slider(
                        "Minimum Engagement (%)", 
                        min_value=0.0, 
                        max_value=float(video_df["engagement"].max()), 
                        value=0.0,
                        step=0.5,
                        key="eng_min_engagement"
                    )
                
                with col2:
                    view_filter = st.selectbox(
                        "View Range",
                        ["All", "<1K", "1K-10K", "10K-100K", "100K-1M", "1M+"],
                        key="eng_view_filter"
                    )
            
            # Apply filters
            filtered_eng_df = video_df[video_df["engagement"] >= min_engagement]
            
            if view_filter != "All":
                if view_filter == "<1K":
                    filtered_eng_df = filtered_eng_df[filtered_eng_df["views"] < 1000]
                elif view_filter == "1K-10K":
                    filtered_eng_df = filtered_eng_df[(filtered_eng_df["views"] >= 1000) & (filtered_eng_df["views"] < 10000)]
                elif view_filter == "10K-100K":
                    filtered_eng_df = filtered_eng_df[(filtered_eng_df["views"] >= 10000) & (filtered_eng_df["views"] < 100000)]
                elif view_filter == "100K-1M":
                    filtered_eng_df = filtered_eng_df[(filtered_eng_df["views"] >= 100000) & (filtered_eng_df["views"] < 1000000)]
                else:  # 1M+
                    filtered_eng_df = filtered_eng_df[filtered_eng_df["views"] >= 1000000]
            
            # Row 1: Engagement vs Duration and Views
            col_chart5, col_chart6 = st.columns(2)
            
            with col_chart5:
                # Engagement vs Duration scatter plot
                if not filtered_eng_df.empty:
                    fig_engagement = px.scatter(
                        filtered_eng_df,
                        x="duration_min",
                        y="engagement",
                        size="views",
                        color="views",
                        title="Engagement Rate vs Video Duration",
                        color_continuous_scale="reds",
                        labels={
                            "duration_min": "Duration (minutes)",
                            "engagement": "Engagement Rate (%)",
                            "views": "Views"
                        },
                        hover_name="title",
                        hover_data=["published_at"]
                    )
                    
                    # Add optimal duration line
                    if not filtered_eng_df.empty:
                        optimal_duration = filtered_eng_df.groupby(pd.cut(filtered_eng_df["duration_min"], bins=10))["engagement"].mean().idxmax().mid
                        fig_engagement.add_vline(
                            x=optimal_duration, 
                            line_dash="dash", 
                            line_color="white",
                            annotation_text=f"Optimal: ~{optimal_duration:.1f} min",
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
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart6:
                # Engagement over time
                if not filtered_eng_df.empty:
                    fig_eng_trend = px.line(
                        filtered_eng_df,
                        x="published_at",
                        y="engagement",
                        title="Engagement Rate Over Time",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"published_at": "Publish Date", "engagement": "Engagement Rate (%)"},
                        hover_name="title",
                        hover_data=["views", "duration_formatted"]
                    )
                    
                    # Add trendline
                    fig_eng_trend.add_scatter(
                        x=filtered_eng_df["published_at"],
                        y=filtered_eng_df["engagement"].rolling(7, min_periods=1).mean(),
                        mode='lines',
                        name='7-Day Avg',
                        line=dict(color='white', width=2, dash='dash')
                    )
                    
                    fig_eng_trend.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_eng_trend, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
            
            # Row 2: Likes vs Comments and Engagement distribution
            col_chart7, col_chart8 = st.columns(2)
            
            with col_chart7:
                # Likes vs Comments scatter plot
                if not filtered_eng_df.empty:
                    fig_likes_comments = px.scatter(
                        filtered_eng_df,
                        x="likes",
                        y="comments",
                        size="views",
                        color="engagement",
                        title="Likes vs Comments (Size by Views, Color by Engagement)",
                        color_continuous_scale="reds",
                        labels={
                            "likes": "Likes",
                            "comments": "Comments",
                            "views": "Views",
                            "engagement": "Engagement Rate (%)"
                        },
                        hover_name="title",
                        hover_data=["published_at", "duration_formatted"]
                    )
                    
                    # Add trendline
                    fig_likes_comments.update_traces(
                        marker=dict(size=12, opacity=0.8),
                        selector=dict(mode='markers')
                    )
                    
                    fig_likes_comments.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_likes_comments, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart8:
                # Engagement distribution
                if not filtered_eng_df.empty:
                    fig_eng_dist = px.histogram(
                        filtered_eng_df,
                        x="engagement",
                        title="Engagement Rate Distribution",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"engagement": "Engagement Rate (%)"},
                        nbins=20
                    )
                    
                    # Add average line
                    avg_engagement = filtered_eng_df["engagement"].mean()
                    fig_eng_dist.add_vline(
                        x=avg_engagement,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Avg: {avg_engagement:.1f}%",
                        annotation_position="top right"
                    )
                    
                    fig_eng_dist.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_eng_dist, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
        
        with tab3:
            # Earnings & Growth Tab
            st.markdown("### Earnings & Growth Analysis")
            
            # Create a container for filters
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    currency_option = st.selectbox(
                        "Currency",
                        ["USD", "INR", "EUR"],
                        key="earn_currency"
                    )
                    
                with col2:
                    cpm_option = st.selectbox(
                        "CPM Range",
                        ["low", "medium", "high"],
                        format_func=lambda x: x.capitalize(),
                        key="earn_cpm"
                    )
            
            # Recalculate earnings with selected options
            earnings_data_filtered = calculate_earnings(filtered_videos, currency_option, cpm_option)
            
            # Convert monthly earnings to DataFrame
            monthly_earnings = []
            for month, data in earnings_data_filtered["monthly_earnings"].items():
                monthly_earnings.append({
                    "month": month,
                    "earnings": data["estimated_earnings"],
                    "views": data["views"],
                    "videos": data["videos"],
                    "earnings_per_video": data["estimated_earnings"] / max(1, data["videos"])
                })
            
            earnings_df = pd.DataFrame(monthly_earnings)
            earnings_df["month"] = pd.to_datetime(earnings_df["month"])
            
            # Row 1: Monthly earnings and earnings per video
            col_chart9, col_chart10 = st.columns(2)
            
            with col_chart9:
                # Monthly earnings
                if not earnings_df.empty:
                    fig_earnings = px.bar(
                        earnings_df,
                        x="month",
                        y="earnings",
                        title=f"Monthly Earnings ({currency_option})",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"month": "Month", "earnings": f"Earnings ({currency_option})"}
                    )
                    
                    # Add trendline
                    fig_earnings.add_scatter(
                        x=earnings_df["month"],
                        y=earnings_df["earnings"].rolling(3, min_periods=1).mean(),
                        mode='lines',
                        name='3-Month Avg',
                        line=dict(color='white', width=2, dash='dash')
                    )
                    
                    # Add peak marker
                    max_month = earnings_df.loc[earnings_df['earnings'].idxmax(), 'month']
                    max_earning = earnings_df.loc[earnings_df['earnings'].idxmax(), 'earnings']
                    fig_earnings.add_vline(
                        x=max_month,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Peak: {max_earning:.0f} {currency_option}",
                        annotation_position="top right"
                    )
                    
                    fig_earnings.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_earnings, use_container_width=True)
                else:
                    st.warning("No earnings data available")
                    
            with col_chart10:
                # Earnings per video
                if not earnings_df.empty:
                    fig_earnings_video = px.line(
                        earnings_df,
                        x="month",
                        y="earnings_per_video",
                        title=f"Earnings per Video ({currency_option})",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"month": "Month", "earnings_per_video": f"Earnings per Video ({currency_option})"}
                    )
                    
                    # Add trendline
                    fig_earnings_video.add_scatter(
                        x=earnings_df["month"],
                        y=earnings_df["earnings_per_video"].rolling(3, min_periods=1).mean(),
                        mode='lines',
                        name='3-Month Avg',
                        line=dict(color='white', width=2, dash='dash')
                    )
                    
                    fig_earnings_video.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_earnings_video, use_container_width=True)
                else:
                    st.warning("No earnings data available")
            
            # Row 2: RPM trend and earnings vs views
            col_chart11, col_chart12 = st.columns(2)
            
            with col_chart11:
                # RPM trend
                if len(earnings_df) > 1:
                    earnings_df['rpm'] = (earnings_df['earnings'] / (earnings_df['views'] / 1000)).round(2)
                    
                    fig_rpm = px.line(
                        earnings_df,
                        x="month",
                        y="rpm",
                        title=f"RPM Trend ({currency_option})",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"month": "Month", "rpm": f"RPM ({currency_option})"}
                    )
                    
                    # Add average line
                    avg_rpm = earnings_df['rpm'].mean()
                    fig_rpm.add_hline(
                        y=avg_rpm,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Avg: {avg_rpm:.2f} {currency_option}",
                        annotation_position="bottom right"
                    )
                    
                    fig_rpm.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_rpm, use_container_width=True)
                else:
                    st.warning("Not enough data for RPM analysis")
                
            with col_chart12:
                # Earnings vs Views
                if not earnings_df.empty:
                    fig_earnings_views = px.scatter(
                        earnings_df,
                        x="views",
                        y="earnings",
                        size="videos",
                        title="Earnings vs Views",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={
                            "views": "Total Views",
                            "earnings": f"Earnings ({currency_option})",
                            "videos": "Videos Count"
                        },
                        trendline="ols"
                    )
                    
                    fig_earnings_views.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    st.plotly_chart(fig_earnings_views, use_container_width=True)
                else:
                    st.warning("No earnings data available")
        
        st.markdown("---")
        
        # Video Performance Table
        st.subheader("🎥 Video Performance Details")
        
        # Create a container for table filters
        with st.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                table_sort = st.selectbox(
                    "Sort By",
                    ["Views", "Likes", "Comments", "Engagement", "Published Date"],
                    key="table_sort"
                )
                
            with col2:
                table_order = st.selectbox(
                    "Order",
                    ["Descending", "Ascending"],
                    key="table_order"
                )
                
            with col3:
                table_rows = st.slider(
                    "Rows to Display",
                    min_value=5,
                    max_value=50,
                    value=10,
                    step=5,
                    key="table_rows"
                )
        
        # Sort table
        sort_column = {
            "Views": "views",
            "Likes": "likes",
            "Comments": "comments",
            "Engagement": "engagement",
            "Published Date": "published_at"
        }[table_sort]
        
        ascending = table_order == "Ascending"
        sorted_df = video_df.sort_values(by=sort_column, ascending=ascending)
        
        # Display table with custom styling
        st.dataframe(
            sorted_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]].head(table_rows),
            column_config={
                "title": st.column_config.TextColumn("Title", width="large"),
                "published_at": st.column_config.DatetimeColumn("Published Date", format="YYYY-MM-DD"),
                "views": st.column_config.NumberColumn("Views", format="%d"),
                "likes": st.column_config.NumberColumn("Likes", format="%d"),
                "comments": st.column_config.NumberColumn("Comments", format="%d"),
                "engagement": st.column_config.NumberColumn("Engagement (%)", format="%.2f"),
                "duration_formatted": "Duration"
            },
            use_container_width=True,
            height=(min(table_rows, 10) * 35 + 35),
            hide_index=True
        )

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
