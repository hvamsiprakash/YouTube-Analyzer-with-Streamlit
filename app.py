# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta
import re

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
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
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 15px;
    }
    
    .section-divider {
        border-top: 2px solid var(--primary-color);
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

# Function to format numbers
def format_number(num):
    if num >= 1000000000:
        return f"{num/1000000000:.1f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

# Function to calculate channel age
def calculate_channel_age(published_at):
    try:
        pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
        delta = relativedelta(datetime.now(), pub_date)
        if delta.years > 0:
            return f"{delta.years} year{'s' if delta.years > 1 else ''}"
        elif delta.months > 0:
            return f"{delta.months} month{'s' if delta.months > 1 else ''}"
        else:
            return f"{delta.days} day{'s' if delta.days > 1 else ''}"
    except:
        return "N/A"

# Function to clean video tags
def clean_tags(tags_list):
    if not tags_list:
        return []
    # Remove special characters and make lowercase
    cleaned = [re.sub(r'[^a-zA-Z0-9\s]', '', tag).lower() for tag in tags_list]
    # Remove empty strings and duplicates
    return list(set([tag for tag in cleaned if tag.strip()]))

# Main dashboard function
def youtube_dashboard():
    st.title("YouTube Pro Analytics Dashboard")
    
    # Channel ID input at top
    col_input1, col_input2 = st.columns([3, 1])
    with col_input1:
        channel_id = st.text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    
    with col_input2:
        st.write("")  # For alignment
        analyze_btn = st.button("Analyze Channel", type="primary")
    
    if not channel_id and not analyze_btn:
        st.stop()
    
    if analyze_btn and not channel_id:
        st.error("Please enter a valid YouTube Channel ID")
        st.stop()
    
    if analyze_btn and channel_id:
        with st.spinner("Fetching and analyzing channel data..."):
            channel_data = get_channel_analytics(channel_id)
            
        if not channel_data:
            st.stop()
            
        # Prepare video data
        video_df = pd.DataFrame(channel_data["videos"])
        video_df["published_at"] = pd.to_datetime(video_df["published_at"], errors="coerce")
        video_df = video_df.dropna(subset=["published_at"])
        video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
        video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
        video_df["engagement"] = ((video_df["likes"] + video_df["comments"]) / video_df["views"].replace(0, 1)) * 100
        
        # Calculate channel age
        channel_age = calculate_channel_age(channel_data["basic_info"]["published_at"])
        
        # Channel header
        st.markdown("---")
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
                <div class="metric-subtext">{len(video_df)} in current analysis</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            avg_engagement = video_df["engagement"].mean()
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Avg Engagement</div>
                <div class="metric-value">{avg_engagement:.1f}%</div>
                <div class="metric-subtext">(Likes + Comments) / Views</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance Charts Section
        st.subheader("Performance Analytics")
        
        # Time range filter
        with st.expander("📅 Time Range Filter", expanded=False):
            col_time1, col_time2 = st.columns(2)
            with col_time1:
                time_range = st.selectbox(
                    "Select Time Range",
                    ["Last 7 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All time"],
                    index=2
                )
            
            now = datetime.now()
            if time_range == "Last 7 days":
                cutoff_date = now - timedelta(days=7)
            elif time_range == "Last 30 days":
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
        
        # Row 1: Views Over Time and Top Videos
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 📈 Views Over Time")
            
            # Group by week/month based on time range
            if len(filtered_videos) > 30:
                freq = "W"  # Weekly for larger datasets
                resample_freq = "Weekly"
            else:
                freq = "D"  # Daily for smaller datasets
                resample_freq = "Daily"
                
            views_over_time = filtered_videos.set_index("published_at")["views"].resample(freq).sum().reset_index()
            
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
                hovermode="x unified",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_views, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 🏆 Top Performing Videos")
            
            # Filters for top videos
            col_top1, col_top2 = st.columns(2)
            with col_top1:
                top_n = st.slider("Number of videos", 5, 20, 10, key="top_n_slider")
            with col_top2:
                sort_by = st.selectbox("Sort by", ["Views", "Likes", "Engagement"], key="top_sort_select")
            
            top_videos = filtered_videos.nlargest(top_n, sort_by.lower())
            
            fig_top_videos = px.bar(
                top_videos, 
                x=sort_by.lower(), 
                y="title",
                orientation='h',
                labels={"title": "Video Title", sort_by.lower(): sort_by},
                color_discrete_sequence=["#FF4B4B"],
                hover_data=["published_at", "duration_formatted", "views", "likes", "comments"]
            )
            fig_top_videos.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="y unified",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig_top_videos, use_container_width=True)
        
        # Row 2: Engagement Analysis and Upload Frequency
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            st.markdown("#### 💬 Engagement Analysis")
            
            # Engagement filters
            col_eng1, col_eng2 = st.columns(2)
            with col_eng1:
                min_views = st.slider("Min views", 0, int(filtered_videos["views"].max()), 1000, key="eng_view_slider")
            with col_eng2:
                duration_filter = st.selectbox("Duration", ["All", "Short (<1 min)", "Medium (1-5 min)", "Long (>5 min)"], key="eng_dur_select")
            
            # Apply filters
            eng_df = filtered_videos[filtered_videos["views"] >= min_views]
            if duration_filter == "Short (<1 min)":
                eng_df = eng_df[eng_df["duration_sec"] < 60]
            elif duration_filter == "Medium (1-5 min)":
                eng_df = eng_df[(eng_df["duration_sec"] >= 60) & (eng_df["duration_sec"] < 300)]
            elif duration_filter == "Long (>5 min)":
                eng_df = eng_df[eng_df["duration_sec"] >= 300]
            
            fig_engagement = px.scatter(
                eng_df, 
                x="views", 
                y="engagement",
                size="likes",
                color="duration_sec",
                labels={"views": "Views", "engagement": "Engagement Rate (%)", "duration_sec": "Duration (sec)"},
                color_continuous_scale="reds",
                hover_name="title",
                hover_data=["published_at", "duration_formatted"]
            )
            fig_engagement.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                hovermode="closest",
                height=400,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_engagement, use_container_width=True)
            
        with col_chart4:
            st.markdown("#### 📅 Upload Frequency")
            
            # Upload frequency analysis
            uploads_by_day = filtered_videos.copy()
            uploads_by_day["day_of_week"] = uploads_by_day["published_at"].dt.day_name()
            uploads_by_day["hour"] = uploads_by_day["published_at"].dt.hour
            
            # Day of week analysis
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            uploads_day = uploads_by_day["day_of_week"].value_counts().reindex(day_order).reset_index()
            uploads_day.columns = ["day", "count"]
            
            fig_upload_day = px.bar(
                uploads_day,
                x="day",
                y="count",
                labels={"day": "Day of Week", "count": "Uploads"},
                color_discrete_sequence=["#FF4B4B"]
            )
            fig_upload_day.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                height=400,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_upload_day, use_container_width=True)


        # Row 3: Video Duration Distribution and Tag Analysis
        col_chart5, col_chart6 = st.columns(2)
        
        with col_chart5:
            st.markdown("#### ⏱️ Video Duration Distribution")
            
            # Duration buckets
            duration_bins = [0, 60, 300, 600, 1800, 3600, float('inf')]
            duration_labels = ["<1 min", "1-5 min", "5-10 min", "10-30 min", "30-60 min", ">60 min"]
            
            duration_df = filtered_videos.copy()
            duration_df["duration_bin"] = pd.cut(
                duration_df["duration_sec"],
                bins=duration_bins,
                labels=duration_labels,
                right=False
            )
            
            duration_counts = duration_df["duration_bin"].value_counts().sort_index()
            
            fig_duration = px.bar(
                duration_counts,
                x=duration_counts.index,
                y=duration_counts.values,
                labels={"x": "Duration", "y": "Number of Videos"},
                color_discrete_sequence=["#FF4B4B"]
            )
            fig_duration.update_layout(
                plot_bgcolor="#1A1D24",
                paper_bgcolor="#0E1117",
                font={"color": "white"},
                height=400,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_duration, use_container_width=True)
            
        with col_chart6:
            st.markdown("#### 🏷️ Tag Analysis")
            
            # Process all tags
            all_tags = []
            for tags in filtered_videos["tags"]:
                if isinstance(tags, list):
                    all_tags.extend(clean_tags(tags))
            
            if not all_tags:
                st.info("No tags found in the analyzed videos")
            else:
                # Get top tags
                tag_counts = pd.Series(all_tags).value_counts().head(20)
                
                fig_tags = px.bar(
                    tag_counts,
                    x=tag_counts.values,
                    y=tag_counts.index,
                    orientation='h',
                    labels={"x": "Usage Count", "y": "Tag"},
                    color_discrete_sequence=["#FF4B4B"]
                )
                fig_tags.update_layout(
                    plot_bgcolor="#1A1D24",
                    paper_bgcolor="#0E1117",
                    font={"color": "white"},
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig_tags, use_container_width=True)
        
        st.markdown("---")
        
        # Revenue Estimation Section
        st.subheader("💰 Revenue Estimation")
        st.markdown("*Estimates based on public view counts and typical CPM ranges*")
        
        col_rev1, col_rev2, col_rev3 = st.columns(3)
        
        with col_rev1:
            currency = st.selectbox("Currency", ["USD", "INR", "EUR"], key="currency_select")
        
        with col_rev2:
            cpm_range = st.selectbox("CPM Range", ["Low", "Medium", "High"], key="cpm_select")
            cpm_ranges = {
                "Low": {"USD": 1.0, "INR": 40, "EUR": 0.9},
                "Medium": {"USD": 3.0, "INR": 120, "EUR": 2.7},
                "High": {"USD": 5.0, "INR": 200, "EUR": 4.5}
            }
            selected_cpm = cpm_ranges[cpm_range][currency]
        
        with col_rev3:
            st.metric("Selected CPM", f"{selected_cpm} {currency}")
        
        # Calculate estimated earnings
        total_views = filtered_videos["views"].sum()
        estimated_earnings = (total_views / 1000) * selected_cpm
        
        col_rev4, col_rev5 = st.columns(2)
        
        with col_rev4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Estimated Earnings</div>
                <div class="metric-value">{currency} {estimated_earnings:,.2f}</div>
                <div class="metric-subtext">Based on {total_views:,} views</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_rev5:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-title">Estimated RPM</div>
                <div class="metric-value">{currency} {(estimated_earnings / (total_views / 1000)) if total_views > 0 else 0:.2f}</div>
                <div class="metric-subtext">Revenue Per 1000 views</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed Video Performance Table
        st.subheader("🎬 Detailed Video Performance")
        
        # Filters for the table
        col_table1, col_table2, col_table3 = st.columns(3)
        
        with col_table1:
            table_min_views = st.slider(
                "Minimum Views", 
                min_value=0, 
                max_value=int(filtered_videos["views"].max()), 
                value=0,
                key="table_views_slider"
            )
            
        with col_table2:
            table_min_engagement = st.slider(
                "Minimum Engagement (%)", 
                min_value=0.0, 
                max_value=float(filtered_videos["engagement"].max()), 
                value=0.0,
                step=0.5,
                key="table_eng_slider"
            )
            
        with col_table3:
            duration_options = ["All"] + duration_labels
            table_duration_filter = st.selectbox(
                "Duration Filter",
                options=duration_options,
                key="table_dur_select"
            )
        
        # Apply filters to table data
        table_data = filtered_videos.copy()
        table_data = table_data[table_data["views"] >= table_min_views]
        table_data = table_data[table_data["engagement"] >= table_min_engagement]
        
        if table_duration_filter != "All":
            selected_bin = duration_labels.index(table_duration_filter)
            min_dur = duration_bins[selected_bin]
            max_dur = duration_bins[selected_bin + 1]
            table_data = table_data[
                (table_data["duration_sec"] >= min_dur) & 
                (table_data["duration_sec"] < max_dur)
            ]
        
        # Display the table
        st.dataframe(
            table_data[[
                "title", "published_at", "views", "likes", "comments", 
                "engagement", "duration_formatted"
            ]].rename(columns={
                "title": "Title",
                "published_at": "Published Date",
                "views": "Views",
                "likes": "Likes",
                "comments": "Comments",
                "engagement": "Engagement (%)",
                "duration_formatted": "Duration"
            }).sort_values("Views", ascending=False),
            height=500,
            use_container_width=True,
            column_config={
                "Title": st.column_config.TextColumn(width="large"),
                "Published Date": st.column_config.DatetimeColumn(format="YYYY-MM-DD"),
                "Views": st.column_config.NumberColumn(format="%,d"),
                "Likes": st.column_config.NumberColumn(format="%,d"),
                "Comments": st.column_config.NumberColumn(format="%,d"),
                "Engagement (%)": st.column_config.NumberColumn(format="%.1f"),
                "Duration": st.column_config.TextColumn()
            }
        )
        
        # Playlists section (if available)
        try:
            # Get channel playlists
            playlists = []
            next_page_token = None
            
            for _ in range(2):  # Max 2 pages (100 playlists)
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
            
            if playlists:
                st.markdown("---")
                st.subheader("🎵 Playlists")
                
                for i, playlist in enumerate(playlists[:5]):  # Show max 5 playlists
                    col_pl1, col_pl2 = st.columns([1, 4])
                    
                    with col_pl1:
                        st.image(playlist["thumbnail"], width=150)
                        
                    with col_pl2:
                        st.markdown(f"##### {playlist['title']}")
                        st.markdown(f"**Videos:** {playlist['item_count']}")
                        st.markdown(f"**Playlist ID:** {playlist['playlist_id']}")
                    
                    if i < len(playlists[:5]) - 1:
                        st.markdown("---")
        except:
            pass
        
        # Disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 12px; color: #AAAAAA;">
        <strong>Disclaimer:</strong> This dashboard uses YouTube Data API to fetch public channel data. 
        Revenue estimates are based on typical CPM ranges and should not be considered exact. 
        Actual earnings may vary based on many factors including audience demographics, 
        content category, and advertiser demand.
        </div>
        """, unsafe_allow_html=True)

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
