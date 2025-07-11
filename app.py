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
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
        background-color: var(--secondary-color) !important;
        color: var(--text-color) !important;
    }
    
    .stApp {
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
    
    .filter-box {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    
    .filter-title {
        color: var(--primary-color);
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }
    
    .section-title {
        color: var(--primary-color);
        font-size: 18px;
        font-weight: 700;
        margin: 20px 0 10px 0;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 5px;
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
        }
    }
    
    # Calculate total views
    total_views = sum(video["views"] for video in videos_data)
    
    # Simplified calculation for dashboard
    if currency == "USD":
        if cpm_range == "low":
            rpm = 1.0
        elif cpm_range == "medium":
            rpm = 2.0
        else:
            rpm = 3.5
    else:
        rpm = 2.0  # Default
    
    total_earnings = (total_views / 1000) * rpm
    
    return {
        "total_earnings": total_earnings,
        "currency": currency,
        "cpm_range": cpm_range,
        "total_views": total_views,
        "estimated_rpm": rpm
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

# Function to get channel age
def get_channel_age(published_at):
    try:
        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        delta = relativedelta(datetime.now(), pub_date)
        return f"{delta.years} years, {delta.months} months"
    except:
        return "N/A"

# Function to generate word cloud
def generate_wordcloud(tags_list):
    if not tags_list:
        return None
    
    # Flatten all tags from all videos
    all_tags = [tag for video_tags in tags_list for tag in video_tags]
    if not all_tags:
        return None
    
    # Count tag frequencies
    tag_freq = Counter(all_tags)
    
    # Generate word cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='#1A1D24',
        colormap='Reds',
        max_words=50
    ).generate_from_frequencies(tag_freq)
    
    # Display with matplotlib
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_facecolor('#1A1D24')
    fig.patch.set_facecolor('#1A1D24')
    
    return fig

# Main dashboard function
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")
    
    # Channel ID input at top
    channel_id = st.text_input("Enter YouTube Channel ID", 
                              placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA",
                              help="Find this in your YouTube channel URL")
    
    if not channel_id:
        st.warning("Please enter a YouTube Channel ID to begin analysis")
        st.stop()
    
    with st.spinner("Fetching and analyzing channel data..."):
        channel_data = get_channel_analytics(channel_id)
        
    if not channel_data:
        st.stop()
    
    # Create DataFrame from videos
    video_df = pd.DataFrame(channel_data["videos"])
    video_df["published_at"] = pd.to_datetime(video_df["published_at"])
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["publish_day"] = video_df["published_at"].dt.day_name()
    video_df["publish_month"] = video_df["published_at"].dt.strftime("%Y-%m")
    
    # Calculate channel age
    channel_age = get_channel_age(channel_data["basic_info"]["published_at"])
    
    # --- Dashboard Layout ---
    
    # Channel Header
    st.markdown("---")
    col_header1, col_header2 = st.columns([1, 3])
    
    with col_header1:
        st.image(channel_data["basic_info"]["thumbnail"], width=150)
        
    with col_header2:
        st.markdown(f"### {channel_data['basic_info']['title']}")
        st.markdown(f"**Channel URL:** youtube.com/channel/{channel_id}")
        st.markdown(f"**Country:** {channel_data['basic_info']['country']}")
        st.markdown(f"**Created:** {datetime.strptime(channel_data['basic_info']['published_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')} ({channel_age})")
    
    st.markdown("---")
    
    # --- Global Filters ---
    st.markdown("### 🔍 Global Filters")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        time_range = st.selectbox(
            "Time Range",
            ["All time", "Last year", "Last 6 months", "Last 90 days", "Last 30 days"],
            key="time_range"
        )
        
    with col_filter2:
        min_views = st.slider(
            "Minimum Views",
            min_value=0,
            max_value=int(video_df["views"].max()),
            value=0,
            step=1000,
            key="min_views"
        )
        
    with col_filter3:
        content_type = st.selectbox(
            "Content Type",
            ["All", "Short (<1 min)", "Medium (1-10 min)", "Long (>10 min)"],
            key="content_type"
        )
    
    # Apply global filters
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
    
    filtered_df = video_df[
        (video_df["published_at"] >= cutoff_date) &
        (video_df["views"] >= min_views)
    ]
    
    if content_type == "Short (<1 min)":
        filtered_df = filtered_df[filtered_df["duration_sec"] < 60]
    elif content_type == "Medium (1-10 min)":
        filtered_df = filtered_df[(filtered_df["duration_sec"] >= 60) & (filtered_df["duration_sec"] < 600)]
    elif content_type == "Long (>10 min)":
        filtered_df = filtered_df[filtered_df["duration_sec"] >= 600]
    
    # --- Performance Overview ---
    st.markdown("## 📊 Channel Performance Overview")
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
            <div class="metric-subtext">{len(filtered_df)} videos in filtered period</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Total Videos</div>
            <div class="metric-value">{format_number(channel_data['statistics']['video_count'])}</div>
            <div class="metric-subtext">{len(filtered_df)} in filtered period</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        # Calculate average engagement
        avg_engagement = filtered_df["engagement"].mean() if not filtered_df.empty else 0
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Avg Engagement</div>
            <div class="metric-value">{avg_engagement:.1f}%</div>
            <div class="metric-subtext">(Likes + Comments)/Views</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- Growth Analytics ---
    st.markdown("## 📈 Growth Analytics")
    
    # Row 1: Views Over Time
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.markdown("### Views Over Time")
        
        # Resample data based on time range
        if time_range in ["Last 30 days", "Last 90 days"]:
            freq = "W"  # Weekly
        elif time_range == "Last 6 months":
            freq = "2W"  # Bi-weekly
        else:
            freq = "M"  # Monthly
            
        views_over_time = filtered_df.set_index("published_at")["views"].resample(freq).sum().reset_index()
        
        fig_views = px.line(
            views_over_time,
            x="published_at",
            y="views",
            labels={"published_at": "Date", "views": "Views"},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig_views.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400
        )
        st.plotly_chart(fig_views, use_container_width=True)
    
    with col_chart2:
        st.markdown("### Performance by Day of Week")
        
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_stats = filtered_df.groupby("publish_day")["views"].mean().reindex(day_order).reset_index()
        
        fig_days = px.bar(
            day_stats,
            x="publish_day",
            y="views",
            labels={"publish_day": "Day of Week", "views": "Avg Views"},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig_days.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400,
            xaxis={"categoryorder": "array", "array": day_order}
        )
        st.plotly_chart(fig_days, use_container_width=True)
    
    # --- Content Analysis ---
    st.markdown("## 📹 Content Analysis")
    
    # Row 1: Top Videos and Duration Distribution
    col_content1, col_content2 = st.columns(2)
    
    with col_content1:
        st.markdown("### Top Performing Videos")
        
        top_videos = filtered_df.nlargest(10, "views")
        fig_top_videos = px.bar(
            top_videos,
            x="views",
            y="title",
            orientation="h",
            labels={"title": "Video Title", "views": "Views"},
            color_discrete_sequence=["#FF4B4B"],
            hover_data=["published_at", "likes", "comments", "duration_formatted"]
        )
        fig_top_videos.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400,
            yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig_top_videos, use_container_width=True)
    
    with col_content2:
        st.markdown("### Video Duration Distribution")
        
        # Categorize videos by duration
        duration_bins = [0, 60, 300, 600, 1800, 3600, float('inf')]
        duration_labels = ["<1 min", "1-5 min", "5-10 min", "10-30 min", "30-60 min", ">60 min"]
        filtered_df["duration_category"] = pd.cut(
            filtered_df["duration_sec"],
            bins=duration_bins,
            labels=duration_labels,
            right=False
        )
        
        duration_stats = filtered_df["duration_category"].value_counts().reset_index()
        duration_stats.columns = ["duration", "count"]
        
        fig_duration = px.pie(
            duration_stats,
            names="duration",
            values="count",
            color_discrete_sequence=px.colors.sequential.Reds,
            hole=0.4
        )
        fig_duration.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_duration, use_container_width=True)


    # --- Engagement Analysis ---
    st.markdown("## 💬 Engagement Analysis")
    
    # Row 1: Engagement Rate and Likes/Comments Ratio
    col_engage1, col_engage2 = st.columns(2)
    
    with col_engage1:
        st.markdown("### Engagement Rate Over Time")
        
        # Calculate engagement rate over time
        engagement_over_time = filtered_df.set_index("published_at")["engagement"].resample('M').mean().reset_index()
        
        fig_engage = px.line(
            engagement_over_time,
            x="published_at",
            y="engagement",
            labels={"published_at": "Date", "engagement": "Engagement Rate (%)"},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig_engage.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400
        )
        st.plotly_chart(fig_engage, use_container_width=True)
    
    with col_engage2:
        st.markdown("### Likes vs Comments Ratio")
        
        # Calculate likes to comments ratio
        filtered_df["likes_comments_ratio"] = filtered_df["likes"] / filtered_df["comments"].replace(0, 1)
        ratio_stats = filtered_df.groupby("publish_month").agg({
            "likes": "sum",
            "comments": "sum"
        }).reset_index()
        ratio_stats["ratio"] = ratio_stats["likes"] / ratio_stats["comments"].replace(0, 1)
        
        fig_ratio = go.Figure()
        fig_ratio.add_trace(go.Bar(
            x=ratio_stats["publish_month"],
            y=ratio_stats["likes"],
            name="Likes",
            marker_color="#FF4B4B"
        ))
        fig_ratio.add_trace(go.Bar(
            x=ratio_stats["publish_month"],
            y=ratio_stats["comments"],
            name="Comments",
            marker_color="#FF9999"
        ))
        fig_ratio.update_layout(
            barmode="group",
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
    
    # --- Tag Analysis ---
    st.markdown("## 🏷️ Tag Analysis")
    
    # Generate word cloud from video tags
    tag_fig = generate_wordcloud(filtered_df["tags"].tolist())
    if tag_fig:
        st.markdown("### Most Frequently Used Tags")
        st.pyplot(tag_fig)
    else:
        st.warning("No tags available for analysis")
    
    # --- Revenue Estimation ---
    st.markdown("## 💰 Revenue Estimation")
    
    # Revenue calculator
    col_rev1, col_rev2 = st.columns(2)
    
    with col_rev1:
        st.markdown("### Earnings Calculator")
        
        # CPM selection
        cpm_range = st.select_slider(
            "Select CPM Range (USD)",
            options=["Low ($1)", "Medium ($3)", "High ($5)"],
            value="Medium ($3)"
        )
        
        # Calculate estimated earnings
        if cpm_range == "Low ($1)":
            rpm = 1.0
        elif cpm_range == "Medium ($3)":
            rpm = 3.0
        else:
            rpm = 5.0
        
        total_views = filtered_df["views"].sum()
        estimated_earnings = (total_views / 1000) * rpm
        
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Estimated Earnings</div>
            <div class="metric-value">${estimated_earnings:,.2f}</div>
            <div class="metric-subtext">Based on {format_number(total_views)} views at ${rpm:.2f} RPM</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("""
        Note: This is a rough estimate only. Actual earnings depend on many factors including:
        - Audience demographics
        - Ad types shown
        - Viewer engagement with ads
        - Seasonality
        """)
    
    with col_rev2:
        st.markdown("### Monthly Revenue Trend")
        
        # Calculate monthly revenue
        monthly_views = filtered_df.groupby("publish_month")["views"].sum().reset_index()
        monthly_views["estimated_revenue"] = (monthly_views["views"] / 1000) * rpm
        
        fig_revenue = px.bar(
            monthly_views,
            x="publish_month",
            y="estimated_revenue",
            labels={"publish_month": "Month", "estimated_revenue": "Estimated Revenue ($)"},
            color_discrete_sequence=["#FF4B4B"]
        )
        fig_revenue.update_layout(
            plot_bgcolor="#1A1D24",
            paper_bgcolor="#0E1117",
            font={"color": "white"},
            height=400
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    # --- Upload Frequency ---
    st.markdown("## 📅 Upload Frequency")
    
    # Create a calendar heatmap of uploads
    upload_dates = filtered_df["published_at"].dt.date.value_counts().reset_index()
    upload_dates.columns = ["date", "uploads"]
    upload_dates["date"] = pd.to_datetime(upload_dates["date"])
    upload_dates["week"] = upload_dates["date"].dt.isocalendar().week
    upload_dates["day"] = upload_dates["date"].dt.dayofweek
    upload_dates["year"] = upload_dates["date"].dt.year
    upload_dates["month"] = upload_dates["date"].dt.month
    
    # Group by week and day
    heatmap_data = upload_dates.groupby(["year", "week", "day"])["uploads"].sum().reset_index()
    
    # Create heatmap
    fig_heatmap = go.Figure(go.Heatmap(
        x=heatmap_data["week"],
        y=heatmap_data["day"],
        z=heatmap_data["uploads"],
        colorscale="Reds",
        hoverongaps=False,
        hovertemplate="Week: %{x}<br>Day: %{y}<br>Uploads: %{z}<extra></extra>"
    ))
    
    # Customize heatmap
    fig_heatmap.update_layout(
        title="Upload Frequency Heatmap",
        height=400,
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        yaxis=dict(
            tickmode="array",
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        ),
        plot_bgcolor="#1A1D24",
        paper_bgcolor="#0E1117",
        font={"color": "white"}
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # --- Video Performance Table ---
    st.markdown("## 🎬 Detailed Video Performance")
    
    # Additional filters for table
    col_table1, col_table2 = st.columns(2)
    
    with col_table1:
        sort_by = st.selectbox(
            "Sort By",
            ["Views (High-Low)", "Likes (High-Low)", "Comments (High-Low)", "Engagement (High-Low)", "Recent First"],
            key="sort_by"
        )
    
    with col_table2:
        rows_to_show = st.slider(
            "Number of Videos to Show",
            min_value=10,
            max_value=100,
            value=20,
            step=10,
            key="rows_to_show"
        )
    
    # Apply sorting
    if sort_by == "Views (High-Low)":
        sorted_df = filtered_df.sort_values("views", ascending=False)
    elif sort_by == "Likes (High-Low)":
        sorted_df = filtered_df.sort_values("likes", ascending=False)
    elif sort_by == "Comments (High-Low)":
        sorted_df = filtered_df.sort_values("comments", ascending=False)
    elif sort_by == "Engagement (High-Low)":
        sorted_df = filtered_df.sort_values("engagement", ascending=False)
    else:
        sorted_df = filtered_df.sort_values("published_at", ascending=False)
    
    # Display the table
    st.dataframe(
        sorted_df.head(rows_to_show)[[
            "title", "published_at", "views", "likes", "comments", 
            "engagement", "duration_formatted"
        ]].rename(columns={
            "title": "Title",
            "published_at": "Published At",
            "views": "Views",
            "likes": "Likes",
            "comments": "Comments",
            "engagement": "Engagement (%)",
            "duration_formatted": "Duration"
        }),
        height=600,
        use_container_width=True
    )
    
    # --- Footer ---
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #AAAAAA; font-size: 12px;">
        <p>YouTube Pro Analytics Dashboard • Data provided by YouTube Data API v3</p>
        <p>Note: All revenue estimates are approximations based on public data only</p>
    </div>
    """, unsafe_allow_html=True)

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
