# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
def set_dark_theme():
    st.markdown("""
    <style>
    :root {
        --primary-color: #FF4B4B;
        --secondary-color: #0E1117;
        --text-color: #FFFFFF;
        --card-bg: #1A1D24;
    }
    
    .main {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }
    
    .sidebar {
        background-color: var(--secondary-color) !important;
        border-right: 1px solid #333 !important;
    }
    
    .sidebar .sidebar-content {
        background-color: var(--secondary-color) !important;
    }
    
    .st-bw, .st-at, .st-cn {
        background-color: var(--secondary-color) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
    }
    
    .metric-box {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-title {
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: var(--text-color);
        font-size: 28px;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .metric-subtext {
        color: #AAAAAA;
        font-size: 12px;
        margin-top: 5px;
    }
    
    .stSelectbox, .stSlider, .stDateInput, .stTextInput {
        background-color: var(--card-bg) !important;
        border-color: #333 !important;
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
        return f"${num/1000000000:.1f}B" if num < 0 else f"{num/1000000000:.1f}B"
    elif num >= 1000000:
        return f"${num/1000000:.1f}M" if num < 0 else f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"${num/1000:.1f}K" if num < 0 else f"{num/1000:.1f}K"
    return f"${num}" if num < 0 else str(num)

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
    st.title("YouTube Pro Analytics Dashboard")
    st.markdown("""
    <style>
    .section-divider {
        border-top: 2px solid #FF4B4B;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("Configuration")
    st.sidebar.markdown("---")
    
    channel_id = st.sidebar.text_input("Enter YouTube Channel ID", key="channel_id", 
                                     placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Earnings Settings")
    
    currency_options = {"USD": "US Dollar", "INR": "Indian Rupee", "EUR": "Euro"}
    selected_currency = st.sidebar.selectbox("Currency", options=list(currency_options.keys()), 
                                           format_func=lambda x: currency_options[x])
    
    cpm_options = {"low": "Low CPM", "medium": "Medium CPM", "high": "High CPM"}
    selected_cpm = st.sidebar.selectbox("CPM Range", options=list(cpm_options.keys()), 
                                      format_func=lambda x: cpm_options[x])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Time Range")
    
    time_range = st.sidebar.selectbox("Data Range", 
                                     ["Last 30 days", "Last 90 days", "Last 6 months", 
                                      "Last year", "Last 2 years", "All time"])
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Analyze Channel", key="analyze_btn", 
                        help="Fetch and analyze channel data"):
        if not channel_id:
            st.error("Please enter a valid YouTube Channel ID")
            st.stop()
            
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
        
        # Calculate earnings
        earnings_data = calculate_earnings(filtered_videos, selected_currency, selected_cpm)
        
        # Create DataFrame for filtered videos
        video_df = pd.DataFrame(filtered_videos)
        video_df["published_at"] = pd.to_datetime(video_df["published_at"])
        video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
        video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
        
        # Convert monthly earnings to DataFrame
        monthly_earnings = []
        for month, data in earnings_data["monthly_earnings"].items():
            monthly_earnings.append({
                "month": month,
                "earnings": data["estimated_earnings"],
                "views": data["views"],
                "videos": data["videos"],
                "earnings_per_video": data["estimated_earnings"] / max(1, data["videos"])
            })
        
        earnings_df = pd.DataFrame(monthly_earnings)
        earnings_df["month"] = pd.to_datetime(earnings_df["month"])
        
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
        st.subheader("Channel Performance Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Subscribers</div>
                <div class="metric-value">{format_number(channel_data['statistics']['subscriber_count'])}</div>
                <div class="metric-subtext">Hidden: {'Yes' if channel_data['statistics']['hidden_subscriber_count'] else 'No'}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Views</div>
                <div class="metric-value">{format_number(channel_data['statistics']['view_count'])}</div>
                <div class="metric-subtext">{len(filtered_videos)} videos in selected period</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Videos</div>
                <div class="metric-value">{format_number(channel_data['statistics']['video_count'])}</div>
                <div class="metric-subtext">{len(filtered_videos)} in selected period</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Estimated Earnings</div>
                <div class="metric-value">{selected_currency} {format_number(earnings_data['total_earnings'])}</div>
                <div class="metric-subtext">RPM: {earnings_data['estimated_rpm']:.2f} {selected_currency}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance Charts
        st.subheader("Performance Analytics")
        
        # Row 1: Views and Earnings
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Views over time
            fig_views = px.line(
                video_df, 
                x="published_at", 
                y="views", 
                title="Video Views Over Time",
                color_discrete_sequence=["#FF4B4B"],
                labels={"published_at": "Publish Date", "views": "Views"}
            )
            fig_views.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400
            )
            st.plotly_chart(fig_views, use_container_width=True)
            
        with col_chart2:
            # Monthly earnings
            if not earnings_df.empty:
                fig_earnings = px.bar(
                    earnings_df, 
                    x="month", 
                    y="earnings",
                    title=f"Monthly Earnings ({selected_currency})",
                    color_discrete_sequence=["#FF4B4B"],
                    labels={"month": "Month", "earnings": "Earnings"}
                )
                fig_earnings.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    hovermode="x unified",
                    height=400
                )
                st.plotly_chart(fig_earnings, use_container_width=True)
        
        # Row 2: Top Videos and Engagement
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            # Top performing videos
            top_videos = video_df.nlargest(10, "views")
            fig_top_videos = px.bar(
                top_videos, 
                x="views", 
                y="title",
                orientation='h',
                title="Top Videos by Views",
                color_discrete_sequence=["#FF4B4B"],
                labels={"title": "Video Title", "views": "Views"},
                hover_data=["published_at", "likes", "comments", "duration_formatted"]
            )
            fig_top_videos.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="y unified",
                height=400,
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig_top_videos, use_container_width=True)
            
        with col_chart4:
            # Engagement rate scatter plot
            fig_engagement = px.scatter(
                video_df, 
                x="views", 
                y="engagement",
                size="likes",
                color="duration_sec",
                title="Engagement Rate vs Views",
                color_continuous_scale="reds",
                labels={"views": "Views", "engagement": "Engagement Rate (%)", "duration_sec": "Duration (sec)"},
                hover_name="title",
                hover_data=["published_at", "likes", "comments"]
            )
            fig_engagement.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="closest",
                height=400
            )
            st.plotly_chart(fig_engagement, use_container_width=True)
        
        st.markdown("---")
        
        # Video Analytics Section
        st.subheader("Video Performance Details")
        
        # Filters
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            min_views = st.slider(
                "Minimum Views", 
                min_value=0, 
                max_value=int(video_df["views"].max()), 
                value=0,
                step=1000
            )
            
        with col_filter2:
            min_likes = st.slider(
                "Minimum Likes", 
                min_value=0, 
                max_value=int(video_df["likes"].max()), 
                value=0,
                step=1000
            )
            
        with col_filter3:
            min_engagement = st.slider(
                "Minimum Engagement (%)", 
                min_value=0.0, 
                max_value=float(video_df["engagement"].max()), 
                value=0.0,
                step=0.5
            )
            
        with col_filter4:
            duration_range = st.slider(
                "Duration Range (minutes)", 
                min_value=0, 
                max_value=int(video_df["duration_sec"].max() // 60) + 1, 
                value=(0, int(video_df["duration_sec"].max() // 60) + 1)
            )
        
        # Apply filters
        filtered_df = video_df[
            (video_df["views"] >= min_views) & 
            (video_df["likes"] >= min_likes) & 
            (video_df["engagement"] >= min_engagement) &
            (video_df["duration_sec"] >= duration_range[0] * 60) &
            (video_df["duration_sec"] <= duration_range[1] * 60)
        ]
        
        # Display metrics about filtered videos
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        
        with col_metric1:
            avg_views = filtered_df["views"].mean()
            st.metric("Average Views", f"{avg_views:,.0f}")
            
        with col_metric2:
            avg_engagement = filtered_df["engagement"].mean()
            st.metric("Average Engagement", f"{avg_engagement:.2f}%")
            
        with col_metric3:
            avg_duration = filtered_df["duration_sec"].mean() / 60
            st.metric("Average Duration", f"{avg_duration:.1f} mins")
        
        # Display filtered results
        st.dataframe(
            filtered_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]].rename(columns={
                "title": "Title",
                "published_at": "Published Date",
                "views": "Views",
                "likes": "Likes",
                "comments": "Comments",
                "engagement": "Engagement (%)",
                "duration_formatted": "Duration"
            }).sort_values("Views", ascending=False),
            height=500,
            use_container_width=True
        )
        
        # Playlists section
        if channel_data["playlists"]:
            st.markdown("---")
            st.subheader("Playlists Performance")
            
            for playlist in channel_data["playlists"][:5]:  # Show max 5 playlists
                col_pl1, col_pl2 = st.columns([1, 4])
                
                with col_pl1:
                    st.image(playlist["thumbnail"], width=150)
                    
                with col_pl2:
                    st.markdown(f"**{playlist['title']}**")
                    st.markdown(f"**Videos:** {playlist['item_count']}")
                    st.markdown(f"**Playlist ID:** {playlist['playlist_id']}")
                
                st.markdown("---")

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
