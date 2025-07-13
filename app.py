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
    
    .chart-container {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .chart-filters {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    .stSelectbox, .stSlider, .stDateInput, .stTextInput {
        background-color: var(--card-bg) !important;
        border-color: #333 !important;
        color: white !important;
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
    
    .st-eb {
        background-color: var(--card-bg) !important;
    }
    
    .st-bb {
        border-bottom: 1px solid #333 !important;
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
                        "category_id": snippet.get("categoryId", ""),
                        "tags": snippet.get("tags", [])
                    })
            
            next_page_token = videos_response.get("nextPageToken")
            if not next_page_token:
                break
        
        # Calculate engagement metrics
        for video in videos:
            video["engagement"] = ((video["likes"] + video["comments"]) / max(1, video["views"])) * 100
        
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
            "videos": sorted(videos, key=lambda x: x["views"], reverse=True)
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

# Function to calculate channel age
def calculate_channel_age(published_at):
    try:
        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        delta = relativedelta(datetime.now(), pub_date)
        return f"{delta.years} years, {delta.months} months"
    except:
        return "N/A"

# Main dashboard function
def youtube_dashboard():
    st.title("YouTube Pro Analytics Dashboard")
    
    # Channel ID input at top
    channel_id = st.text_input("Enter YouTube Channel ID", 
                              placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA",
                              help="Find this in your YouTube channel URL")
    
    if not channel_id:
        st.warning("Please enter a YouTube Channel ID to begin analysis")
        return
    
    with st.spinner("Fetching and analyzing channel data..."):
        channel_data = get_channel_analytics(channel_id)
        
    if not channel_data:
        return
    
    # Create DataFrame for videos
    video_df = pd.DataFrame(channel_data["videos"])
    
    # Convert published_at to datetime and handle errors
    try:
        video_df["published_at"] = pd.to_datetime(video_df["published_at"])
    except:
        st.error("Error processing video dates. Some data may not display correctly.")
        return
    
    # Calculate additional metrics
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["published_date"] = video_df["published_at"].dt.date
    
    # Channel header
    col_header1, col_header2 = st.columns([1, 3])
    
    with col_header1:
        st.image(channel_data["basic_info"]["thumbnail"], width=150)
        
    with col_header2:
        st.markdown(f"### {channel_data['basic_info']['title']}")
        st.markdown(f"**Channel URL:** youtube.com/channel/{channel_id}")
        st.markdown(f"**Country:** {channel_data['basic_info']['country']}")
        st.markdown(f"**Created:** {datetime.strptime(channel_data['basic_info']['published_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')}")
        st.markdown(f"**Channel Age:** {calculate_channel_age(channel_data['basic_info']['published_at'])}")
    
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
            <div class="metric-subtext">{len(video_df)} videos analyzed</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Total Videos</div>
            <div class="metric-value">{format_number(channel_data['statistics']['video_count'])}</div>
            <div class="metric-subtext">Avg: {channel_data['statistics']['view_count']/max(1, channel_data['statistics']['video_count']):,.0f} views/video</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        # Earnings settings
        col_earn1, col_earn2 = st.columns(2)
        with col_earn1:
            currency = st.selectbox("Currency", ["USD", "INR", "EUR"], key="currency")
        with col_earn2:
            cpm_range = st.selectbox("CPM Range", ["low", "medium", "high"], 
                                  format_func=lambda x: x.capitalize(), key="cpm_range")
        
        earnings_data = calculate_earnings(channel_data["videos"], currency, cpm_range)
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Estimated Earnings</div>
            <div class="metric-value">{currency} {format_number(earnings_data['total_earnings'])}</div>
            <div class="metric-subtext">RPM: {earnings_data['estimated_rpm']:.2f} {currency}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance Charts Section
    st.subheader("Performance Analytics")
    
    # Row 1: Views Over Time and Upload Frequency
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Video Views Over Time</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Time range filter
            time_range = st.selectbox(
                "Time Range",
                ["All time", "Last year", "Last 6 months", "Last 90 days", "Last 30 days"],
                key="views_time_range"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Apply time filter
            now = datetime.now()
            if time_range == "Last 30 days":
                cutoff_date = now - timedelta(days=30)
            elif time_range == "Last 90 days":
                cutoff_date = now - timedelta(days=90)
            elif time_range == "Last 6 months":
                cutoff_date = now - relativedelta(months=6)
            elif time_range == "Last year":
                cutoff_date = now - relativedelta(years=1)
            else:
                cutoff_date = datetime.min
                
            filtered_df = video_df[video_df["published_at"] >= cutoff_date]
            
            # Views over time
            fig_views = px.line(
                filtered_df, 
                x="published_at", 
                y="views", 
                title="",
                color_discrete_sequence=["#FF4B4B"],
                labels={"published_at": "Publish Date", "views": "Views"}
            )
            fig_views.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_views, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_chart2:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-header"><h4>Upload Frequency</h4></div>', unsafe_allow_html=True)
            
            # Calculate upload frequency by week
            upload_freq = video_df.groupby(pd.Grouper(key="published_at", freq="W-MON"))["video_id"].count().reset_index()
            upload_freq.columns = ["week_start", "video_count"]
            
            fig_upload = px.bar(
                upload_freq,
                x="week_start",
                y="video_count",
                title="",
                color_discrete_sequence=["#FF4B4B"],
                labels={"week_start": "Week Starting", "video_count": "Videos Uploaded"}
            )
            fig_upload.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_upload, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Row 2: Top Videos and Engagement Rate
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Top Performing Videos</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Top N filter
            top_n = st.selectbox(
                "Show Top",
                [10, 25, 50],
                index=0,
                key="top_n_videos"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Top performing videos
            top_videos = video_df.nlargest(top_n, "views")
            
            fig_top_videos = px.bar(
                top_videos, 
                x="views", 
                y="title",
                orientation='h',
                title="",
                color_discrete_sequence=["#FF4B4B"],
                labels={"title": "Video Title", "views": "Views"},
                hover_data=["published_date", "likes", "comments", "duration_formatted", "engagement"]
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
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_chart4:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Engagement Analysis</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Engagement filter
            min_views = st.number_input(
                "Min Views",
                min_value=0,
                max_value=int(video_df["views"].max()),
                value=1000,
                step=1000,
                key="engagement_min_views"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Filter videos
            engagement_df = video_df[video_df["views"] >= min_views]
            
            # Engagement rate scatter plot
            fig_engagement = px.scatter(
                engagement_df, 
                x="views", 
                y="engagement",
                size="likes",
                color="duration_sec",
                title="",
                color_continuous_scale="reds",
                labels={"views": "Views", "engagement": "Engagement Rate (%)", "duration_sec": "Duration (sec)"},
                hover_name="title",
                hover_data=["published_date", "likes", "comments"]
            )
            fig_engagement.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="closest",
                height=400
            )
            st.plotly_chart(fig_engagement, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Row 3: Video Duration and Tag Analysis
    col_chart5, col_chart6 = st.columns(2)
    
    with col_chart5:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Video Duration Distribution</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Duration bucket filter
            duration_bins = st.selectbox(
                "Duration Buckets",
                ["All", "Short (<1 min)", "Medium (1-5 min)", "Long (5-10 min)", "Extended (>10 min)"],
                key="duration_bins"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Filter by duration
            duration_df = video_df.copy()
            if duration_bins == "Short (<1 min)":
                duration_df = duration_df[duration_df["duration_sec"] < 60]
            elif duration_bins == "Medium (1-5 min)":
                duration_df = duration_df[(duration_df["duration_sec"] >= 60) & (duration_df["duration_sec"] < 300)]
            elif duration_bins == "Long (5-10 min)":
                duration_df = duration_df[(duration_df["duration_sec"] >= 300) & (duration_df["duration_sec"] < 600)]
            elif duration_bins == "Extended (>10 min)":
                duration_df = duration_df[duration_df["duration_sec"] >= 600]
            
            # Create duration distribution
            duration_df["duration_min"] = duration_df["duration_sec"] / 60
            fig_duration = px.histogram(
                duration_df,
                x="duration_min",
                nbins=20,
                title="",
                color_discrete_sequence=["#FF4B4B"],
                labels={"duration_min": "Duration (minutes)", "count": "Number of Videos"}
            )
            fig_duration.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                showlegend=False,
                xaxis_title="Duration (minutes)",
                yaxis_title="Number of Videos"
            )
            st.plotly_chart(fig_duration, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_chart6:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Tag Analysis</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Top N tags filter
            top_tags = st.selectbox(
                "Show Top",
                [10, 20, 30],
                index=0,
                key="top_tags"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Extract and count tags
            all_tags = []
            for tags in video_df["tags"]:
                if isinstance(tags, list):
                    all_tags.extend([tag.lower() for tag in tags])
            
            if all_tags:
                tag_counts = pd.Series(all_tags).value_counts().head(top_tags)
                tag_df = pd.DataFrame({"tag": tag_counts.index, "count": tag_counts.values})
                
                fig_tags = px.bar(
                    tag_df,
                    x="count",
                    y="tag",
                    orientation='h',
                    title="",
                    color_discrete_sequence=["#FF4B4B"],
                    labels={"tag": "Tag", "count": "Usage Count"}
                )
                fig_tags.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    hovermode="y unified",
                    height=400,
                    yaxis={'categoryorder':'total ascending'}
                )
                st.plotly_chart(fig_tags, use_container_width=True)
            else:
                st.warning("No tags found in video metadata")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Row 4: Performance by Day of Week and Earnings Breakdown
    col_chart7, col_chart8 = st.columns(2)
    
    with col_chart7:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="chart-header"><h4>Performance by Day of Week</h4></div>', unsafe_allow_html=True)
            
            # Calculate day of week performance
            day_df = video_df.copy()
            day_df["day_of_week"] = day_df["published_at"].dt.day_name()
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            # Aggregate by day
            day_stats = day_df.groupby("day_of_week").agg({
                "views": "mean",
                "engagement": "mean",
                "video_id": "count"
            }).reindex(day_order).reset_index()
            
            # Create figure with secondary y-axis
            fig_day = go.Figure()
            
            # Add views trace
            fig_day.add_trace(
                go.Bar(
                    x=day_stats["day_of_week"],
                    y=day_stats["views"],
                    name="Avg Views",
                    marker_color="#FF4B4B"
                )
            )
            
            # Add engagement trace
            fig_day.add_trace(
                go.Scatter(
                    x=day_stats["day_of_week"],
                    y=day_stats["engagement"],
                    name="Avg Engagement %",
                    line=dict(color="#FFA726", width=3),
                    yaxis="y2"
                )
            )
            
            # Update layout
            fig_day.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                yaxis=dict(
                    title="Average Views",
                    titlefont=dict(color="#FF4B4B"),
                    tickfont=dict(color="#FF4B4B")
                ),
                yaxis2=dict(
                    title="Engagement Rate (%)",
                    titlefont=dict(color="#FFA726"),
                    tickfont=dict(color="#FFA726"),
                    overlaying="y",
                    side="right"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_day, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_chart8:
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            
            # Chart header with filters
            st.markdown("""
            <div class="chart-header">
                <h4>Earnings Breakdown</h4>
                <div class="chart-filters">
            """, unsafe_allow_html=True)
            
            # Time range filter
            earnings_range = st.selectbox(
                "Time Range",
                ["All time", "Last year", "Last 6 months"],
                key="earnings_range"
            )
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Filter earnings data
            earnings_df = pd.DataFrame(earnings_data["monthly_earnings"]).T.reset_index()
            earnings_df.columns = ["month", "views", "videos", "earnings"]
            earnings_df["month"] = pd.to_datetime(earnings_df["month"])
            
            if earnings_range == "Last year":
                cutoff_date = datetime.now() - relativedelta(years=1)
                earnings_df = earnings_df[earnings_df["month"] >= cutoff_date]
            elif earnings_range == "Last 6 months":
                cutoff_date = datetime.now() - relativedelta(months=6)
                earnings_df = earnings_df[earnings_df["month"] >= cutoff_date]
            
            # Create earnings breakdown
            fig_earnings = go.Figure()
            
            fig_earnings.add_trace(
                go.Bar(
                    x=earnings_df["month"],
                    y=earnings_df["earnings"],
                    name="Earnings",
                    marker_color="#FF4B4B"
                )
            )
            
            fig_earnings.add_trace(
                go.Scatter(
                    x=earnings_df["month"],
                    y=earnings_df["earnings"].cumsum(),
                    name="Cumulative Earnings",
                    line=dict(color="#FFA726", width=3),
                    yaxis="y2"
                )
            )
            
            fig_earnings.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                yaxis=dict(
                    title=f"Monthly Earnings ({earnings_data['currency']})",
                    titlefont=dict(color="#FF4B4B"),
                    tickfont=dict(color="#FF4B4B")
                ),
                yaxis2=dict(
                    title=f"Cumulative Earnings ({earnings_data['currency']})",
                    titlefont=dict(color="#FFA726"),
                    tickfont=dict(color="#FFA726"),
                    overlaying="y",
                    side="right"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_earnings, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Video Performance Details Section
    st.markdown("---")
    st.subheader("Video Performance Details")
    
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Filters row
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            min_views = st.slider(
                "Minimum Views", 
                min_value=0, 
                max_value=int(video_df["views"].max()), 
                value=0,
                step=1000,
                key="table_min_views"
            )
            
        with col_filter2:
            min_likes = st.slider(
                "Minimum Likes", 
                min_value=0, 
                max_value=int(video_df["likes"].max()), 
                value=0,
                step=1000,
                key="table_min_likes"
            )
            
        with col_filter3:
            min_engagement = st.slider(
                "Minimum Engagement (%)", 
                min_value=0.0, 
                max_value=float(video_df["engagement"].max()), 
                value=0.0,
                step=0.5,
                key="table_min_engagement"
            )
            
        with col_filter4:
            duration_range = st.slider(
                "Duration Range (minutes)", 
                min_value=0, 
                max_value=int(video_df["duration_sec"].max() // 60) + 1, 
                value=(0, int(video_df["duration_sec"].max() // 60) + 1),
                key="table_duration_range"
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
            filtered_df[["title", "published_date", "views", "likes", "comments", "engagement", "duration_formatted"]].rename(columns={
                "title": "Title",
                "published_date": "Published Date",
                "views": "Views",
                "likes": "Likes",
                "comments": "Comments",
                "engagement": "Engagement (%)",
                "duration_formatted": "Duration"
            }).sort_values("Views", ascending=False),
            height=500,
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Disclaimer about earnings estimation
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #1A1D24; padding: 15px; border-radius: 8px; border-left: 4px solid #FF4B4B;">
        <p style="color: #AAAAAA; font-size: 14px;">
        <strong>Note about earnings estimates:</strong> The earnings calculations are estimates only based on public view counts and 
        typical CPM (Cost Per Mille) ranges. Actual earnings may vary significantly based on factors like audience 
        demographics, content category, seasonality, and advertiser demand. These estimates should not be considered 
        financial advice or exact predictions of YouTube revenue.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
