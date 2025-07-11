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
    
    .stDataFrame {
        background-color: var(--card-bg) !important;
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
    
    .graph-container {
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: var(--card-bg);
    }
    
    .filter-container {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    
    .css-1aumxhk {
        background-color: var(--secondary-color) !important;
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
    st.title("YouTube Pro Analytics Dashboard")
    
    # Initialize session state variables
    if 'channel_data' not in st.session_state:
        st.session_state.channel_data = None
    if 'filtered_videos' not in st.session_state:
        st.session_state.filtered_videos = []
    if 'time_range' not in st.session_state:
        st.session_state.time_range = "All time"
    
    # Channel input form
    with st.form("channel_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            channel_id = st.text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
        with col2:
            st.write("")  # For alignment
            st.write("")
            analyze_btn = st.form_submit_button("Analyze Channel")
    
    if analyze_btn and channel_id:
        with st.spinner("Fetching and analyzing channel data..."):
            st.session_state.channel_data = get_channel_analytics(channel_id)
            
            if st.session_state.channel_data:
                # Create DataFrame for videos
                video_df = pd.DataFrame(st.session_state.channel_data["videos"])
                video_df["published_at"] = pd.to_datetime(video_df["published_at"])
                video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
                video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
                
                # Apply initial time filter (all time)
                st.session_state.filtered_videos = video_df.copy()
                st.session_state.time_range = "All time"
    
    # Display dashboard if we have channel data
    if st.session_state.channel_data:
        # Channel header
        col_header1, col_header2 = st.columns([1, 3])
        
        with col_header1:
            st.image(st.session_state.channel_data["basic_info"]["thumbnail"], width=150)
            
        with col_header2:
            st.markdown(f"### {st.session_state.channel_data['basic_info']['title']}")
            st.markdown(f"**Channel URL:** youtube.com/channel/{channel_id}")
            st.markdown(f"**Country:** {st.session_state.channel_data['basic_info']['country']}")
            st.markdown(f"**Created:** {datetime.strptime(st.session_state.channel_data['basic_info']['published_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')}")
            if st.session_state.channel_data["basic_info"]["topics"]:
                st.markdown("**Topics:** " + ", ".join([topic.split('/')[-1].replace('_', ' ') for topic in st.session_state.channel_data["basic_info"]["topics"][:3]]))
        
        st.markdown("---")
        
        # Key Metrics
        st.subheader("Channel Performance Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Subscribers</div>
                <div class="metric-value">{format_number(st.session_state.channel_data['statistics']['subscriber_count'])}</div>
                <div class="metric-subtext">Hidden: {'Yes' if st.session_state.channel_data['statistics']['hidden_subscriber_count'] else 'No'}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Views</div>
                <div class="metric-value">{format_number(st.session_state.channel_data['statistics']['view_count'])}</div>
                <div class="metric-subtext">{len(st.session_state.filtered_videos)} videos in selected period</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Total Videos</div>
                <div class="metric-value">{format_number(st.session_state.channel_data['statistics']['video_count'])}</div>
                <div class="metric-subtext">{len(st.session_state.filtered_videos)} in selected period</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            avg_engagement = st.session_state.filtered_videos["engagement"].mean() if not st.session_state.filtered_videos.empty else 0
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Avg Engagement</div>
                <div class="metric-value">{avg_engagement:.2f}%</div>
                <div class="metric-subtext">{(st.session_state.filtered_videos['likes'].sum() + st.session_state.filtered_videos['comments'].sum()) / max(1, st.session_state.filtered_videos['views'].sum()) * 100:.2f}% overall</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Time range filter
        with st.expander("📅 Time Range Filter", expanded=True):
            time_options = ["All time", "Last 30 days", "Last 90 days", "Last 6 months", "Last year", "Last 2 years"]
            selected_time = st.radio("Select time range:", time_options, index=time_options.index(st.session_state.time_range), horizontal=True)
            
            if selected_time != st.session_state.time_range:
                st.session_state.time_range = selected_time
                
                # Calculate cutoff date
                now = datetime.now()
                if selected_time == "Last 30 days":
                    cutoff_date = now - timedelta(days=30)
                elif selected_time == "Last 90 days":
                    cutoff_date = now - timedelta(days=90)
                elif selected_time == "Last 6 months":
                    cutoff_date = now - relativedelta(months=6)
                elif selected_time == "Last year":
                    cutoff_date = now - relativedelta(years=1)
                elif selected_time == "Last 2 years":
                    cutoff_date = now - relativedelta(years=2)
                else:  # All time
                    cutoff_date = datetime.min
                
                # Apply filter without reloading
                video_df = pd.DataFrame(st.session_state.channel_data["videos"])
                video_df["published_at"] = pd.to_datetime(video_df["published_at"])
                st.session_state.filtered_videos = video_df[video_df["published_at"] >= cutoff_date]
        
        # Performance Charts - Row 1
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            with st.container():
                st.subheader("📈 Views Over Time")
                
                # Filter options for this graph
                with st.expander("⚙️ Graph Settings", expanded=False):
                    min_views = st.slider("Minimum Views", 0, int(st.session_state.filtered_videos["views"].max()), 0, key="views_min")
                    max_duration = st.slider("Max Duration (min)", 0, 120, 60, key="views_duration")
                
                # Apply filters
                filtered = st.session_state.filtered_videos[
                    (st.session_state.filtered_videos["views"] >= min_views) & 
                    (st.session_state.filtered_videos["duration_sec"] <= max_duration * 60)
                ]
                
                if not filtered.empty:
                    fig_views = px.line(
                        filtered, 
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
                else:
                    st.warning("No videos match the current filters")
        
        with col_chart2:
            with st.container():
                st.subheader("📊 Top Performing Videos")
                
                # Filter options for this graph
                with st.expander("⚙️ Graph Settings", expanded=False):
                    top_n = st.slider("Number of Videos", 5, 20, 10, key="top_n")
                    sort_by = st.selectbox("Sort By", ["views", "likes", "engagement"], key="sort_by")
                
                # Get top videos
                top_videos = st.session_state.filtered_videos.nlargest(top_n, sort_by)
                
                if not top_videos.empty:
                    fig_top_videos = px.bar(
                        top_videos, 
                        x=sort_by, 
                        y="title",
                        orientation='h',
                        title="",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"title": "Video Title", sort_by: sort_by.capitalize()},
                        hover_data=["published_at", "views", "likes", "duration_formatted"]
                    )
                    fig_top_videos.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="y unified",
                        height=400,
                        yaxis={'categoryorder':'total ascending'},
                        showlegend=False
                    )
                    st.plotly_chart(fig_top_videos, use_container_width=True)
                else:
                    st.warning("No videos match the current filters")

        # Performance Charts - Row 2
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            with st.container():
                st.subheader("📉 Engagement Analysis")
                
                # Filter options for this graph
                with st.expander("⚙️ Graph Settings", expanded=False):
                    min_engagement = st.slider("Min Engagement %", 0.0, 20.0, 0.0, key="min_eng")
                    view_range = st.slider("View Range", 0, int(st.session_state.filtered_videos["views"].max()), 
                                      (0, int(st.session_state.filtered_videos["views"].max())), key="view_range")
                
                # Apply filters
                filtered = st.session_state.filtered_videos[
                    (st.session_state.filtered_videos["engagement"] >= min_engagement) & 
                    (st.session_state.filtered_videos["views"] >= view_range[0]) & 
                    (st.session_state.filtered_videos["views"] <= view_range[1])
                ]
                
                if not filtered.empty:
                    fig_engagement = px.scatter(
                        filtered, 
                        x="views", 
                        y="engagement",
                        size="likes",
                        color="duration_sec",
                        title="",
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
                else:
                    st.warning("No videos match the current filters")
        
        with col_chart4:
            with st.container():
                st.subheader("⏱️ Duration Distribution")
                
                # Filter options for this graph
                with st.expander("⚙️ Graph Settings", expanded=False):
                    duration_bins = st.selectbox("Bin Size", ["5 min", "10 min", "30 min", "1 hour"], key="duration_bins")
                    min_views_dur = st.slider("Minimum Views", 0, int(st.session_state.filtered_videos["views"].max()), 0, key="min_views_dur")
                
                # Convert bin size to seconds
                if duration_bins == "5 min":
                    bin_size = 300
                elif duration_bins == "10 min":
                    bin_size = 600
                elif duration_bins == "30 min":
                    bin_size = 1800
                else:
                    bin_size = 3600
                
                # Apply filters
                filtered = st.session_state.filtered_videos[st.session_state.filtered_videos["views"] >= min_views_dur]
                
                if not filtered.empty:
                    # Create duration bins
                    filtered["duration_bin"] = (filtered["duration_sec"] // bin_size) * bin_size
                    duration_counts = filtered["duration_bin"].value_counts().sort_index().reset_index()
                    duration_counts.columns = ["duration_sec", "count"]
                    
                    # Format duration labels
                    duration_counts["duration_label"] = duration_counts["duration_sec"].apply(
                        lambda x: f"{x//3600}h {(x%3600)//60}m" if x >= 3600 else f"{x//60}m"
                    )
                    
                    fig_duration = px.bar(
                        duration_counts, 
                        x="duration_label", 
                        y="count",
                        title="",
                        color_discrete_sequence=["#FF4B4B"],
                        labels={"duration_label": "Duration Range", "count": "Number of Videos"}
                    )
                    fig_duration.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="x unified",
                        height=400,
                        showlegend=False,
                        xaxis={'categoryorder':'total descending'}
                    )
                    st.plotly_chart(fig_duration, use_container_width=True)
                else:
                    st.warning("No videos match the current filters")
        
        st.markdown("---")
        
        # Performance by Day of Week
        st.subheader("📅 Performance by Day of Week")
        
        # Filter options
        with st.expander("⚙️ Filter Settings", expanded=False):
            metric = st.selectbox("Metric to Analyze", ["views", "likes", "comments", "engagement"], key="dow_metric")
            min_views_dow = st.slider("Minimum Views", 0, int(st.session_state.filtered_videos["views"].max()), 0, key="min_views_dow")
        
        # Apply filters
        filtered = st.session_state.filtered_videos[st.session_state.filtered_videos["views"] >= min_views_dow]
        
        if not filtered.empty:
            # Extract day of week
            filtered["day_of_week"] = filtered["published_at"].dt.day_name()
            
            # Calculate average metric by day
            dow_stats = filtered.groupby("day_of_week")[metric].mean().reset_index()
            
            # Order days properly
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow_stats["day_of_week"] = pd.Categorical(dow_stats["day_of_week"], categories=days_order, ordered=True)
            dow_stats = dow_stats.sort_values("day_of_week")
            
            fig_dow = px.bar(
                dow_stats, 
                x="day_of_week", 
                y=metric,
                title="",
                color_discrete_sequence=["#FF4B4B"],
                labels={"day_of_week": "Day of Week", metric: metric.capitalize()}
            )
            fig_dow.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="x unified",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_dow, use_container_width=True)
        else:
            st.warning("No videos match the current filters")
        
        st.markdown("---")
        
        # Video Details Table
        st.subheader("🎬 Video Performance Details")
        
        # Filters for the table
        with st.expander("⚙️ Table Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                table_min_views = st.slider(
                    "Minimum Views", 
                    min_value=0, 
                    max_value=int(st.session_state.filtered_videos["views"].max()), 
                    value=0,
                    key="table_min_views"
                )
                
            with col2:
                table_min_likes = st.slider(
                    "Minimum Likes", 
                    min_value=0, 
                    max_value=int(st.session_state.filtered_videos["likes"].max()), 
                    value=0,
                    key="table_min_likes"
                )
                
            with col3:
                duration_range = st.slider(
                    "Duration Range (minutes)", 
                    min_value=0, 
                    max_value=int(st.session_state.filtered_videos["duration_sec"].max() // 60) + 1, 
                    value=(0, int(st.session_state.filtered_videos["duration_sec"].max() // 60) + 1),
                    key="table_duration"
                )
        
        # Apply filters
        filtered_table = st.session_state.filtered_videos[
            (st.session_state.filtered_videos["views"] >= table_min_views) & 
            (st.session_state.filtered_videos["likes"] >= table_min_likes) &
            (st.session_state.filtered_videos["duration_sec"] >= duration_range[0] * 60) &
            (st.session_state.filtered_videos["duration_sec"] <= duration_range[1] * 60)
        ]
        
        # Display metrics about filtered videos
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        
        with col_metric1:
            avg_views = filtered_table["views"].mean() if not filtered_table.empty else 0
            st.metric("Average Views", f"{avg_views:,.0f}")
            
        with col_metric2:
            avg_engagement = filtered_table["engagement"].mean() if not filtered_table.empty else 0
            st.metric("Average Engagement", f"{avg_engagement:.2f}%")
            
        with col_metric3:
            avg_duration = filtered_table["duration_sec"].mean() / 60 if not filtered_table.empty else 0
            st.metric("Average Duration", f"{avg_duration:.1f} mins")
        
        # Display filtered results
        if not filtered_table.empty:
            st.dataframe(
                filtered_table[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]].rename(columns={
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
        else:
            st.warning("No videos match the current filters")

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
