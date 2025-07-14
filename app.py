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
import base64

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

# Function to encode image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Custom CSS for dark theme with red accents
def set_dark_theme():
    youtube_logo = get_base64_image("images/youtube_png.png")
    
    st.markdown(f"""
    <style>
    :root {{
        --primary-color: #FF0000;
        --secondary-color: #0E1117;
        --text-color: #FFFFFF;
        --card-bg: #1A1D24;
        --dark-red: #8B0000;
        --medium-red: #CC0000;
        --light-red: #FF3333;
    }}
    
    .header-container {{
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }}
    
    .youtube-logo {{
        width: 50px;
        height: 35px;
    }}
    
    .main {{
        background-color: var(--secondary-color);
        color: var(--text-color);
    }}
    
    .st-bw, .st-at, .st-cn {{
        background-color: var(--secondary-color) !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: var(--primary-color) !important;
    }}
    
    .metric-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-bottom: 30px;
    }}
    
    .metric-card {{
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border-left: 4px solid var(--primary-color);
        transition: transform 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(255, 0, 0, 0.3);
    }}
    
    .metric-title {{
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }}
    
    .metric-value {{
        color: var(--text-color);
        font-size: 28px;
        font-weight: 700;
        margin: 10px 0;
    }}
    
    .metric-change {{
        font-size: 12px;
        display: flex;
        align-items: center;
    }}
    
    .positive {{
        color: #00FF00;
    }}
    
    .negative {{
        color: #FF0000;
    }}
    
    .neutral {{
        color: #AAAAAA;
    }}
    
    .chart-container {{
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    
    .chart-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }}
    
    .chart-title {{
        color: var(--text-color);
        font-size: 18px;
        font-weight: 700;
    }}
    
    .chart-filters {{
        display: flex;
        gap: 10px;
        align-items: center;
    }}
    
    .filter-label {{
        color: #AAAAAA;
        font-size: 12px;
        margin-right: 5px;
    }}
    
    .stSelectbox, .stSlider, .stDateInput, .stTextInput {{
        background-color: var(--card-bg) !important;
        border-color: #333 !important;
        color: white !important;
    }}
    
    .st-bb {{
        background-color: var(--card-bg) !important;
    }}
    
    .stDataFrame {{
        background-color: var(--card-bg) !important;
    }}
    
    .css-1aumxhk {{
        background-color: var(--secondary-color) !important;
    }}
    
    .css-1v0mbdj {{
        border: 1px solid #333 !important;
    }}
    
    .tab-content {{
        padding: 15px 0;
    }}
    
    .section-divider {{
        border-top: 2px solid var(--medium-red);
        margin: 20px 0;
        opacity: 0.5;
    }}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--card-bg);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--medium-red);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-color);
    }}
    
    /* Hide Streamlit footer and hamburger menu */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
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

# Main dashboard function
def youtube_dashboard():
    # Custom header with YouTube logo
    st.markdown("""
    <div class="header-container">
        <img src="data:image/png;base64,{}" class="youtube-logo">
        <h1>YouTube Pro Analytics Dashboard</h1>
    </div>
    """.format(get_base64_image("images/youtube_png.png")), unsafe_allow_html=True)
    
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
        
        # Calculate earnings with default settings
        earnings_data = calculate_earnings(filtered_videos)
        
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
        
        # Performance Analytics Section
        st.subheader("📈 Performance Analytics")
        
        # Tab layout for different chart types
        tab1, tab2, tab3 = st.tabs(["Views Analysis", "Engagement Metrics", "Earnings & Growth"])
        
        with tab1:
            # Views Analysis Tab
            st.markdown("### Video Views Analysis")
            
            # Create filters container
            with st.expander("🔍 Filter Options", expanded=True):
                col1, col2, col3 = st.columns(3)
                
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
                        ["All", "Short (<5 min)", "Medium (5-15 min)", "Long (15+ min)"],
                        key="views_duration_filter"
                    )
                
                with col3:
                    sort_order = st.selectbox(
                        "Sort By",
                        ["Most Views", "Least Views", "Newest", "Oldest"],
                        key="views_sort_order"
                    )
            
            # Apply filters
            filtered_df = video_df[video_df["views"] >= min_views]
            
            if duration_filter != "All":
                if duration_filter == "Short (<5 min)":
                    filtered_df = filtered_df[filtered_df["duration_min"] < 5]
                elif duration_filter == "Medium (5-15 min)":
                    filtered_df = filtered_df[(filtered_df["duration_min"] >= 5) & (filtered_df["duration_min"] < 15)]
                else:  # Long (15+ min)
                    filtered_df = filtered_df[filtered_df["duration_min"] >= 15]
            
            # Apply sorting
            if sort_order == "Most Views":
                filtered_df = filtered_df.sort_values("views", ascending=False)
            elif sort_order == "Least Views":
                filtered_df = filtered_df.sort_values("views", ascending=True)
            elif sort_order == "Newest":
                filtered_df = filtered_df.sort_values("published_at", ascending=False)
            else:  # Oldest
                filtered_df = filtered_df.sort_values("published_at", ascending=True)
            
            # Display metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                total_views = filtered_df["views"].sum()
                st.metric("Total Filtered Views", f"{format_number(total_views)}")
            
            with col_metric2:
                avg_views = filtered_df["views"].mean()
                st.metric("Average Views", f"{format_number(avg_views)}")
            
            with col_metric3:
                best_video = filtered_df.iloc[0] if not filtered_df.empty else None
                if best_video is not None:
                    st.metric("Top Video Views", f"{format_number(best_video['views'])}", 
                              help=f"Title: {best_video['title'][:50]}{'...' if len(best_video['title']) > 50 else ''}")
            
            # Row 1: Views over time and heatmap
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Views over time with trendline
                if not filtered_df.empty:
                    fig_views = px.line(
                        filtered_df, 
                        x="published_at", 
                        y="views",
                        title="Video Views Over Time",
                        labels={"published_at": "Publish Date", "views": "Views"},
                        hover_name="title",
                        hover_data=["engagement", "duration_formatted"]
                    )
                    
                    # Add markers for individual videos
                    fig_views.add_trace(
                        go.Scatter(
                            x=filtered_df["published_at"],
                            y=filtered_df["views"],
                            mode='markers',
                            name='Videos',
                            marker=dict(color='#FF4B4B', size=8),
                            hoverinfo='text',
                            hovertext=filtered_df["title"]
                        )
                    )
                    
                    fig_views.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=500,
                        showlegend=False
                    )
                    st.plotly_chart(fig_views, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart2:
                # Views by day of week
                if not filtered_df.empty:
                    fig_day = px.bar(
                        filtered_df.groupby('publish_day')['views'].sum().reset_index(),
                        x="publish_day",
                        y="views",
                        title="Total Views by Day of Week",
                        labels={"publish_day": "Day of Week", "views": "Total Views"}
                    )
                    
                    # Add average line
                    avg_views = filtered_df['views'].sum() / 7
                    fig_day.add_hline(
                        y=avg_views,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Average: {format_number(avg_views)}",
                        annotation_position="top right"
                    )
                    
                    fig_day.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=500,
                        xaxis={'categoryorder': 'array', 'categoryarray': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
                    )
                    fig_day.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_day, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
            
            # Row 2: Views distribution and duration analysis
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # Views distribution
                if not filtered_df.empty:
                    fig_dist = px.histogram(
                        filtered_df,
                        x="views",
                        nbins=20,
                        title="Views Distribution",
                        labels={"views": "Views"}
                    )
                    
                    fig_dist.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_dist.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_dist, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart4:
                # Views vs Duration
                if not filtered_df.empty:
                    fig_duration = px.scatter(
                        filtered_df,
                        x="duration_min",
                        y="views",
                        title="Views vs Video Duration",
                        labels={"duration_min": "Duration (minutes)", "views": "Views"},
                        trendline="lowess",
                        trendline_color_override="white"
                    )
                    
                    fig_duration.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_duration.update_traces(marker=dict(color='#FF4B4B', size=10))
                    st.plotly_chart(fig_duration, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
        
        with tab2:
            # Engagement Metrics Tab
            st.markdown("### Engagement Metrics Analysis")
            
            # Create filters container
            with st.expander("🔍 Filter Options", expanded=True):
                col1, col2, col3 = st.columns(3)
                
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
                        ["All", "Under 1K", "1K-10K", "10K-100K", "100K+"],
                        key="eng_view_filter"
                    )
                
                with col3:
                    sort_order = st.selectbox(
                        "Sort By",
                        ["Highest Engagement", "Lowest Engagement", "Most Likes", "Most Comments"],
                        key="eng_sort_order"
                    )
            
            # Apply filters
            filtered_df = video_df[video_df["engagement"] >= min_engagement]
            
            if view_filter != "All":
                if view_filter == "Under 1K":
                    filtered_df = filtered_df[filtered_df["views"] < 1000]
                elif view_filter == "1K-10K":
                    filtered_df = filtered_df[(filtered_df["views"] >= 1000) & (filtered_df["views"] < 10000)]
                elif view_filter == "10K-100K":
                    filtered_df = filtered_df[(filtered_df["views"] >= 10000) & (filtered_df["views"] < 100000)]
                else:  # 100K+
                    filtered_df = filtered_df[filtered_df["views"] >= 100000]
            
            # Apply sorting
            if sort_order == "Highest Engagement":
                filtered_df = filtered_df.sort_values("engagement", ascending=False)
            elif sort_order == "Lowest Engagement":
                filtered_df = filtered_df.sort_values("engagement", ascending=True)
            elif sort_order == "Most Likes":
                filtered_df = filtered_df.sort_values("likes", ascending=False)
            else:  # Most Comments
                filtered_df = filtered_df.sort_values("comments", ascending=False)
            
            # Display metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                avg_engagement = filtered_df["engagement"].mean() if not filtered_df.empty else 0
                st.metric("Average Engagement", f"{avg_engagement:.2f}%")
            
            with col_metric2:
                total_likes = filtered_df["likes"].sum()
                st.metric("Total Likes", f"{format_number(total_likes)}")
            
            with col_metric3:
                total_comments = filtered_df["comments"].sum()
                st.metric("Total Comments", f"{format_number(total_comments)}")
            
            # Row 1: Engagement trends and correlation
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Engagement over time
                if not filtered_df.empty:
                    fig_eng_trend = px.line(
                        filtered_df,
                        x="published_at",
                        y="engagement",
                        title="Engagement Rate Over Time",
                        labels={"published_at": "Publish Date", "engagement": "Engagement Rate (%)"},
                        hover_name="title",
                        hover_data=["views", "duration_formatted"]
                    )
                    
                    # Add markers
                    fig_eng_trend.add_trace(
                        go.Scatter(
                            x=filtered_df["published_at"],
                            y=filtered_df["engagement"],
                            mode='markers',
                            name='Videos',
                            marker=dict(color='#FF4B4B', size=8),
                            hoverinfo='text',
                            hovertext=filtered_df["title"]
                        )
                    )
                    
                    # Add average line
                    avg_eng = filtered_df["engagement"].mean()
                    fig_eng_trend.add_hline(
                        y=avg_eng,
                        line_dash="dash",
                        line_color="white",
                        annotation_text=f"Average: {avg_eng:.2f}%",
                        annotation_position="top right"
                    )
                    
                    fig_eng_trend.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=500,
                        showlegend=False
                    )
                    st.plotly_chart(fig_eng_trend, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart2:
                # Likes vs Comments
                if not filtered_df.empty:
                    fig_likes_comments = px.scatter(
                        filtered_df,
                        x="likes",
                        y="comments",
                        title="Likes vs Comments",
                        labels={"likes": "Likes", "comments": "Comments"},
                        color="engagement",
                        color_continuous_scale="reds",
                        size="views",
                        hover_name="title",
                        hover_data=["published_at", "duration_formatted"]
                    )
                    
                    fig_likes_comments.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=500
                    )
                    st.plotly_chart(fig_likes_comments, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
            
            # Row 2: Engagement distribution and by duration
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # Engagement distribution
                if not filtered_df.empty:
                    fig_eng_dist = px.histogram(
                        filtered_df,
                        x="engagement",
                        nbins=20,
                        title="Engagement Rate Distribution",
                        labels={"engagement": "Engagement Rate (%)"}
                    )
                    
                    fig_eng_dist.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_eng_dist.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_eng_dist, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
                
            with col_chart4:
                # Engagement by duration
                if not filtered_df.empty:
                    # Bin durations
                    filtered_df['duration_bin'] = pd.cut(
                        filtered_df['duration_min'],
                        bins=[0, 5, 10, 15, 20, 30, float('inf')],
                        labels=['<5m', '5-10m', '10-15m', '15-20m', '20-30m', '30m+']
                    )
                    
                    fig_eng_duration = px.box(
                        filtered_df,
                        x="duration_bin",
                        y="engagement",
                        title="Engagement by Video Duration",
                        labels={"duration_bin": "Duration Range", "engagement": "Engagement Rate (%)"}
                    )
                    
                    fig_eng_duration.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_eng_duration.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_eng_duration, use_container_width=True)
                else:
                    st.warning("No videos match the selected filters")
        
        with tab3:
            # Earnings & Growth Tab
            st.markdown("### Earnings & Growth Analysis")
            
            # Create filters container
            with st.expander("🔍 Earnings Settings", expanded=True):
                col1, col2, col3 = st.columns(3)
                
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
                
                with col3:
                    time_period = st.selectbox(
                        "Time Period",
                        ["Monthly", "Quarterly", "Yearly"],
                        key="earn_time_period"
                    )
            
            # Recalculate earnings with selected options
            earnings_data_filtered = calculate_earnings(filtered_videos, currency_option, cpm_option)
            
            # Convert monthly earnings to DataFrame
            monthly_earnings_filtered = []
            for month, data in earnings_data_filtered["monthly_earnings"].items():
                monthly_earnings_filtered.append({
                    "month": month,
                    "earnings": data["estimated_earnings"],
                    "views": data["views"],
                    "videos": data["videos"],
                    "earnings_per_video": data["estimated_earnings"] / max(1, data["videos"])
                })
            
            earnings_df = pd.DataFrame(monthly_earnings_filtered)
            earnings_df["month"] = pd.to_datetime(earnings_df["month"])
            
            # Aggregate by time period
            if time_period == "Quarterly":
                earnings_df['period'] = earnings_df['month'].dt.to_period('Q').astype(str)
                earnings_df = earnings_df.groupby('period').agg({
                    'earnings': 'sum',
                    'views': 'sum',
                    'videos': 'sum'
                }).reset_index()
                earnings_df['earnings_per_video'] = earnings_df['earnings'] / earnings_df['videos']
            elif time_period == "Yearly":
                earnings_df['period'] = earnings_df['month'].dt.year.astype(str)
                earnings_df = earnings_df.groupby('period').agg({
                    'earnings': 'sum',
                    'views': 'sum',
                    'videos': 'sum'
                }).reset_index()
                earnings_df['earnings_per_video'] = earnings_df['earnings'] / earnings_df['videos']
            else:  # Monthly
                earnings_df['period'] = earnings_df['month'].dt.strftime('%Y-%m')
            
            # Display metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                total_earnings = earnings_df["earnings"].sum()
                st.metric(f"Total Estimated Earnings", f"{currency_option} {format_number(total_earnings)}")
            
            with col_metric2:
                rpm = earnings_data_filtered["estimated_rpm"]
                st.metric("Average RPM", f"{currency_option} {rpm:.2f}")
            
            with col_metric3:
                earnings_per_video = total_earnings / len(filtered_videos) if len(filtered_videos) > 0 else 0
                st.metric("Earnings per Video", f"{currency_option} {format_number(earnings_per_video)}")
            
            # Row 1: Earnings trends and RPM
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Earnings over time
                if not earnings_df.empty:
                    fig_earnings = px.bar(
                        earnings_df,
                        x="period",
                        y="earnings",
                        title=f"Estimated Earnings ({currency_option})",
                        labels={"period": "Period", "earnings": f"Earnings ({currency_option})"}
                    )
                    
                    # Add trendline
                    fig_earnings.add_trace(
                        go.Scatter(
                            x=earnings_df["period"],
                            y=earnings_df["earnings"],
                            mode='lines+markers',
                            name='Trend',
                            line=dict(color='white', width=2)
                        )
                    )
                    
                    fig_earnings.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="x unified",
                        height=500
                    )
                    fig_earnings.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_earnings, use_container_width=True)
                else:
                    st.warning("No earnings data available")
                
            with col_chart2:
                # RPM trend
                if len(earnings_df) > 1:
                    earnings_df['rpm'] = (earnings_df['earnings'] / (earnings_df['views'] / 1000)).round(2)
                    
                    fig_rpm = px.line(
                        earnings_df,
                        x="period",
                        y="rpm",
                        title="RPM (Revenue Per Mille) Trend",
                        labels={"period": "Period", "rpm": f"RPM ({currency_option})"}
                    )
                    
                    # Add markers
                    fig_rpm.add_trace(
                        go.Scatter(
                            x=earnings_df["period"],
                            y=earnings_df["rpm"],
                            mode='markers',
                            marker=dict(color='#FF4B4B', size=8)
                        )
                    )
                    
                    fig_rpm.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=500
                    )
                    st.plotly_chart(fig_rpm, use_container_width=True)
                else:
                    st.warning("Not enough data for RPM analysis")
            
            # Row 2: Earnings vs Views and per video
            col_chart3, col_chart4 = st.columns(2)
            
            with col_chart3:
                # Earnings vs Views
                if not earnings_df.empty:
                    fig_earn_views = px.scatter(
                        earnings_df,
                        x="views",
                        y="earnings",
                        title="Earnings vs Views",
                        labels={"views": "Views", "earnings": f"Earnings ({currency_option})"},
                        size="videos",
                        trendline="lowess",
                        trendline_color_override="white"
                    )
                    
                    fig_earn_views.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_earn_views.update_traces(marker=dict(color='#FF4B4B'))
                    st.plotly_chart(fig_earn_views, use_container_width=True)
                else:
                    st.warning("No earnings data available")
                
            with col_chart4:
                # Earnings per video
                if not earnings_df.empty:
                    fig_earn_video = px.bar(
                        earnings_df,
                        x="period",
                        y="earnings_per_video",
                        title=f"Earnings per Video ({currency_option})",
                        labels={"period": "Period", "earnings_per_video": f"Earnings per Video ({currency_option})"}
                    )
                    
                    fig_earn_video.update_layout(
                        plot_bgcolor="#1A1D24",
                        paper_bgcolor="#0E1117",
                        font={"color": "white"},
                        hovermode="closest",
                        height=400
                    )
                    fig_earn_video.update_traces(marker_color='#FF4B4B')
                    st.plotly_chart(fig_earn_video, use_container_width=True)
                else:
                    st.warning("No earnings data available")
        
        st.markdown("---")
        
        # Video Performance Table
        st.subheader("🎥 Video Performance Details")
        
        # Create filters container
        with st.expander("🔍 Table Filters", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                table_sort = st.selectbox(
                    "Sort By",
                    ["Views", "Likes", "Comments", "Engagement", "Published Date", "Duration"],
                    key="table_sort"
                )
                
            with col2:
                table_order = st.selectbox(
                    "Order",
                    ["Descending", "Ascending"],
                    key="table_order"
                )
        
        # Sort table
        sort_column = {
            "Views": "views",
            "Likes": "likes",
            "Comments": "comments",
            "Engagement": "engagement",
            "Published Date": "published_at",
            "Duration": "duration_sec"
        }[table_sort]
        
        ascending = table_order == "Ascending"
        sorted_df = video_df.sort_values(by=sort_column, ascending=ascending)
        
        # Display table with performance metrics
        st.dataframe(
            sorted_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]],
            column_config={
                "title": "Title",
                "published_at": "Published Date",
                "views": st.column_config.NumberColumn("Views", format="%d"),
                "likes": st.column_config.NumberColumn("Likes", format="%d"),
                "comments": st.column_config.NumberColumn("Comments", format="%d"),
                "engagement": st.column_config.NumberColumn("Engagement (%)", format="%.2f"),
                "duration_formatted": "Duration"
            },
            use_container_width=True,
            height=500
        )

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
