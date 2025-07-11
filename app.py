# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
from collections import Counter

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
    
    .filter-container {
        background-color: var(--card-bg);
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    .section-divider {
        border-top: 2px solid #FF4B4B;
        margin: 20px 0;
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
                    
                    video_data = {
                        "title": snippet.get("title", "N/A"),
                        "video_id": video["id"],
                        "published_at": snippet.get("publishedAt", "N/A"),
                        "duration": details.get("duration", "PT0M"),
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "category_id": snippet.get("categoryId", "")
                    }
                    
                    # Extract tags if available
                    if "tags" in snippet:
                        video_data["tags"] = snippet["tags"]
                    
                    videos.append(video_data)
            
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

# Function to calculate channel age
def get_channel_age(published_at):
    try:
        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        delta = relativedelta(datetime.now(), pub_date)
        return f"{delta.years} years, {delta.months} months"
    except:
        return "N/A"

# Function to get most common tags
def get_top_tags(videos, top_n=10):
    all_tags = []
    for video in videos:
        if "tags" in video:
            all_tags.extend(video["tags"])
    
    if not all_tags:
        return []
    
    tag_counter = Counter(all_tags)
    return tag_counter.most_common(top_n)

# Function to create upload frequency heatmap data
def create_upload_frequency_data(videos):
    upload_dates = []
    for video in videos:
        try:
            pub_date = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ")
            upload_dates.append(pub_date)
        except:
            continue
    
    if not upload_dates:
        return pd.DataFrame()
    
    df = pd.DataFrame(upload_dates, columns=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["weekday"] = df["date"].dt.weekday
    df["week"] = df["date"].dt.isocalendar().week
    
    # Group by year and week
    heatmap_data = df.groupby(["year", "week"]).size().reset_index(name="uploads")
    return heatmap_data

# Main dashboard function
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")
    st.markdown("Analyze your channel performance with professional insights")
    
    # Channel ID input at top
    channel_id = st.text_input("Enter YouTube Channel ID", 
                              placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA",
                              help="Find this in your YouTube channel URL")
    
    if not channel_id:
        st.info("Please enter a YouTube Channel ID to begin analysis")
        st.stop()
    
    with st.spinner("Fetching and analyzing channel data..."):
        channel_data = get_channel_analytics(channel_id)
    
    if not channel_data:
        st.stop()
    
    # Convert videos to DataFrame
    video_df = pd.DataFrame(channel_data["videos"])
    video_df["published_at"] = pd.to_datetime(video_df["published_at"])
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["engagement"] = ((video_df["likes"] + video_df["comments"]) / video_df["views"]) * 100
    video_df["published_date"] = video_df["published_at"].dt.date
    video_df["published_weekday"] = video_df["published_at"].dt.day_name()
    video_df["published_month"] = video_df["published_at"].dt.strftime("%Y-%m")
    
    # Calculate channel age
    channel_age = get_channel_age(channel_data["basic_info"]["published_at"])
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Performance", "🎥 Content Analysis"])
    
    with tab1:
        # Channel header
        col_header1, col_header2 = st.columns([1, 3])
        
        with col_header1:
            st.image(channel_data["basic_info"]["thumbnail"], width=150)
            
        with col_header2:
            st.markdown(f"### {channel_data['basic_info']['title']}")
            st.markdown(f"**Channel URL:** youtube.com/channel/{channel_id}")
            st.markdown(f"**Country:** {channel_data['basic_info']['country']}")
            st.markdown(f"**Channel Age:** {channel_age}")
            if channel_data["basic_info"]["topics"]:
                st.markdown("**Topics:** " + ", ".join([topic.split('/')[-1].replace('_', ' ') for topic in channel_data["basic_info"]["topics"][:3]]))
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
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
                <div class="metric-subtext">Showing {len(video_df)} most recent</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            avg_views = video_df["views"].mean()
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Avg. Views/Video</div>
                <div class="metric-value">{format_number(avg_views)}</div>
                <div class="metric-subtext">Median: {format_number(video_df['views'].median())}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Views and Subscribers Growth
        st.subheader("Views Growth Over Time")
        
        # Filter container for this section
        with st.expander("🔍 Filter Options", expanded=False):
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                time_range = st.selectbox(
                    "Time Range",
                    ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All time"],
                    key="views_time_range"
                )
                
            with col_filter2:
                granularity = st.selectbox(
                    "Granularity",
                    ["Daily", "Weekly", "Monthly"],
                    key="views_granularity"
                )
        
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
        else:  # All time
            cutoff_date = datetime.min
            
        filtered_videos = video_df[video_df["published_at"] >= cutoff_date]
        
        # Prepare data based on granularity
        if granularity == "Daily":
            group_col = "published_date"
        elif granularity == "Weekly":
            group_col = pd.Grouper(key="published_at", freq="W-MON")
        else:  # Monthly
            group_col = pd.Grouper(key="published_at", freq="M")
        
        views_data = filtered_videos.groupby(group_col)["views"].sum().reset_index()
        
        # Plot views over time
        fig_views = px.line(
            views_data, 
            x=group_col if isinstance(group_col, str) else views_data[group_col.key],
            y="views", 
            title=f"Views Over Time ({time_range})",
            color_discrete_sequence=["#FF4B4B"],
            labels={group_col if isinstance(group_col, str) else group_col.key: "Date", "views": "Views"}
        )
        
        fig_views.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            hovermode="x unified",
            height=400
        )
        
        st.plotly_chart(fig_views, use_container_width=True)
        
        # Upload Frequency Heatmap
        st.subheader("Upload Frequency")
        
        heatmap_data = create_upload_frequency_data(channel_data["videos"])
        
        if not heatmap_data.empty:
            fig_heatmap = px.density_heatmap(
                heatmap_data,
                x="week",
                y="year",
                z="uploads",
                title="Uploads by Week and Year",
                color_continuous_scale="reds",
                labels={"week": "Week of Year", "year": "Year", "uploads": "Uploads"}
            )
            
            fig_heatmap.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                height=400
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning("Could not generate upload frequency heatmap - insufficient data")



        # Performance by Weekday
        st.subheader("Performance by Day of Week")
        
        weekday_data = video_df.groupby("published_weekday")["views"].mean().reset_index()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_data["published_weekday"] = pd.Categorical(weekday_data["published_weekday"], categories=weekday_order, ordered=True)
        weekday_data = weekday_data.sort_values("published_weekday")
        
        fig_weekday = px.bar(
            weekday_data,
            x="published_weekday",
            y="views",
            title="Average Views by Day of Week",
            color_discrete_sequence=["#FF4B4B"],
            labels={"published_weekday": "Day of Week", "views": "Average Views"}
        )
        
        fig_weekday.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400
        )
        
        st.plotly_chart(fig_weekday, use_container_width=True)
        
    with tab2:
        # Top Performing Videos
        st.subheader("Top Performing Videos")
        
        with st.expander("🔍 Filter Options", expanded=False):
            col_filter3, col_filter4 = st.columns(2)
            
            with col_filter3:
                min_views = st.slider(
                    "Minimum Views", 
                    min_value=0, 
                    max_value=int(video_df["views"].max()), 
                    value=10000,
                    step=1000,
                    key="top_videos_min_views"
                )
                
            with col_filter4:
                duration_filter = st.selectbox(
                    "Duration Range",
                    ["All", "Shorts (<1 min)", "Medium (1-10 min)", "Long (>10 min)"],
                    key="top_videos_duration"
                )
        
        # Apply filters
        filtered_top = video_df[video_df["views"] >= min_views]
        
        if duration_filter == "Shorts (<1 min)":
            filtered_top = filtered_top[filtered_top["duration_sec"] < 60]
        elif duration_filter == "Medium (1-10 min)":
            filtered_top = filtered_top[(filtered_top["duration_sec"] >= 60) & (filtered_top["duration_sec"] <= 600)]
        elif duration_filter == "Long (>10 min)":
            filtered_top = filtered_top[filtered_top["duration_sec"] > 600]
        
        # Display top videos
        fig_top_videos = px.bar(
            filtered_top.nlargest(20, "views"),
            x="views",
            y="title",
            orientation='h',
            title=f"Top Videos (Filtered: {len(filtered_top)} videos)",
            color="engagement",
            color_continuous_scale="reds",
            labels={"title": "Video Title", "views": "Views", "engagement": "Engagement %"},
            hover_data=["published_at", "likes", "comments", "duration_formatted"]
        )
        
        fig_top_videos.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            hovermode="y unified",
            height=600,
            yaxis={'categoryorder':'total ascending'}
        )
        
        st.plotly_chart(fig_top_videos, use_container_width=True)
        
        # Engagement Analysis
        st.subheader("Engagement Analysis")
        
        with st.expander("🔍 Filter Options", expanded=False):
            col_filter5, col_filter6 = st.columns(2)
            
            with col_filter5:
                engagement_time_range = st.selectbox(
                    "Time Range",
                    ["Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All time"],
                    key="engagement_time_range"
                )
                
            with col_filter6:
                top_n_videos = st.slider(
                    "Show Top N Videos",
                    min_value=5,
                    max_value=50,
                    value=20,
                    key="engagement_top_n"
                )
        
        # Apply time filter
        now = datetime.now()
        if engagement_time_range == "Last 30 days":
            engagement_cutoff = now - timedelta(days=30)
        elif engagement_time_range == "Last 90 days":
            engagement_cutoff = now - timedelta(days=90)
        elif engagement_time_range == "Last 6 months":
            engagement_cutoff = now - relativedelta(months=6)
        elif engagement_time_range == "Last year":
            engagement_cutoff = now - relativedelta(years=1)
        else:  # All time
            engagement_cutoff = datetime.min
            
        engagement_filtered = video_df[video_df["published_at"] >= engagement_cutoff]
        
        # Engagement scatter plot
        fig_engagement = px.scatter(
            engagement_filtered.nlargest(top_n_videos, "views"),
            x="views",
            y="engagement",
            size="likes",
            color="duration_sec",
            title=f"Engagement Rate vs Views (Top {top_n_videos} Videos)",
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
            height=500
        )
        
        st.plotly_chart(fig_engagement, use_container_width=True)
        
        # Estimated Earnings
        st.subheader("Estimated Earnings")
        
        with st.expander("🔍 Earnings Settings", expanded=False):
            col_earn1, col_earn2 = st.columns(2)
            
            with col_earn1:
                earnings_currency = st.selectbox(
                    "Currency",
                    ["USD", "INR", "EUR"],
                    key="earnings_currency"
                )
                
            with col_earn2:
                earnings_cpm = st.selectbox(
                    "CPM Range",
                    ["low", "medium", "high"],
                    format_func=lambda x: {"low": "Low ($1-$3)", "medium": "Medium ($3-$5)", "high": "High ($5+)"}[x],
                    key="earnings_cpm"
                )
        
        earnings_data = calculate_earnings(video_df, earnings_currency, earnings_cpm)
        
        if not earnings_data["monthly_earnings"].empty:
            monthly_earnings = []
            for month, data in earnings_data["monthly_earnings"].items():
                monthly_earnings.append({
                    "month": month,
                    "earnings": data["estimated_earnings"],
                    "views": data["views"],
                    "videos": data["videos"]
                })
            
            earnings_df = pd.DataFrame(monthly_earnings)
            earnings_df["month"] = pd.to_datetime(earnings_df["month"])
            
            # Earnings chart
            fig_earnings = px.bar(
                earnings_df,
                x="month",
                y="earnings",
                title=f"Estimated Monthly Earnings ({earnings_currency}) - {earnings_cpm} CPM",
                color_discrete_sequence=["#FF4B4B"],
                labels={"month": "Month", "earnings": f"Earnings ({earnings_currency})"},
                hover_data=["views", "videos"]
            )
            
            fig_earnings.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400
            )
            
            st.plotly_chart(fig_earnings, use_container_width=True)
            
            # Earnings metrics
            col_earn3, col_earn4, col_earn5 = st.columns(3)
            
            with col_earn3:
                st.metric(
                    "Total Estimated Earnings",
                    f"{earnings_currency} {earnings_data['total_earnings']:,.2f}"
                )
                
            with col_earn4:
                st.metric(
                    "Estimated RPM",
                    f"{earnings_currency} {earnings_data['estimated_rpm']:.2f}"
                )
                
            with col_earn5:
                st.metric(
                    "Total Views in Period",
                    f"{format_number(earnings_data['total_views'])}"
                )
            
            st.caption("Note: Earnings estimates are based on public view counts and typical CPM ranges. Actual earnings may vary significantly based on audience demographics, content type, and advertiser demand.")
        
    with tab3:
        # Video Duration Analysis
        st.subheader("Video Duration Distribution")
        
        # Create duration buckets
        duration_bins = [0, 60, 300, 600, 1800, 3600, float('inf')]
        duration_labels = ["<1 min", "1-5 min", "5-10 min", "10-30 min", "30-60 min", ">60 min"]
        video_df["duration_bucket"] = pd.cut(video_df["duration_sec"], bins=duration_bins, labels=duration_labels)
        
        # Duration distribution
        duration_dist = video_df.groupby("duration_bucket").size().reset_index(name="count")
        
        fig_duration = px.bar(
            duration_dist,
            x="duration_bucket",
            y="count",
            title="Video Duration Distribution",
            color_discrete_sequence=["#FF4B4B"],
            labels={"duration_bucket": "Duration Range", "count": "Number of Videos"}
        )
        
        fig_duration.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400
        )
        
        st.plotly_chart(fig_duration, use_container_width=True)
        
        # Duration vs Performance
        st.subheader("Duration vs Performance")
        
        duration_stats = video_df.groupby("duration_bucket").agg({
            "views": "mean",
            "engagement": "mean",
            "likes": "mean"
        }).reset_index()
        
        fig_duration_stats = px.scatter(
            duration_stats,
            x="duration_bucket",
            y="views",
            size="engagement",
            color="likes",
            title="Average Performance by Duration Range",
            color_continuous_scale="reds",
            labels={
                "duration_bucket": "Duration Range",
                "views": "Average Views",
                "engagement": "Engagement Rate (%)",
                "likes": "Average Likes"
            },
            hover_data=["engagement", "likes"]
        )
        
        fig_duration_stats.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=500
        )
        
        st.plotly_chart(fig_duration_stats, use_container_width=True)
        
        # Tag Analysis
        st.subheader("Tag Analysis")
        
        top_tags = get_top_tags(channel_data["videos"], top_n=15)
        
        if top_tags:
            tags_df = pd.DataFrame(top_tags, columns=["tag", "count"])
            
            fig_tags = px.bar(
                tags_df,
                x="count",
                y="tag",
                orientation='h',
                title="Most Frequently Used Tags",
                color_discrete_sequence=["#FF4B4B"],
                labels={"tag": "Tag", "count": "Usage Count"}
            )
            
            fig_tags.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                height=500,
                yaxis={'categoryorder':'total ascending'}
            )
            
            st.plotly_chart(fig_tags, use_container_width=True)
            
            # Tag performance analysis
            tag_performance = []
            for tag, _ in top_tags:
                tag_videos = [v for v in channel_data["videos"] if "tags" in v and tag in v["tags"]]
                if tag_videos:
                    avg_views = sum(v["views"] for v in tag_videos) / len(tag_videos)
                    avg_engagement = sum((v["likes"] + v["comments"]) / v["views"] for v in tag_videos if v["views"] > 0) * 100 / len(tag_videos)
                    tag_performance.append({
                        "tag": tag,
                        "avg_views": avg_views,
                        "avg_engagement": avg_engagement,
                        "video_count": len(tag_videos)
                    })
            
            if tag_performance:
                tag_perf_df = pd.DataFrame(tag_performance)
                
                fig_tag_perf = px.scatter(
                    tag_perf_df,
                    x="avg_views",
                    y="avg_engagement",
                    size="video_count",
                    color="video_count",
                    title="Tag Performance Analysis",
                    color_continuous_scale="reds",
                    hover_name="tag",
                    labels={
                        "avg_views": "Average Views",
                        "avg_engagement": "Average Engagement (%)",
                        "video_count": "Videos with Tag"
                    }
                )
                
                fig_tag_perf.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    height=500
                )
                
                st.plotly_chart(fig_tag_perf, use_container_width=True)
        else:
            st.warning("No tags found in video metadata")

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
