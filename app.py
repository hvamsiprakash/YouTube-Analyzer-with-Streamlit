import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta

# --- SETTINGS ---
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"  # <- Put your API key here

# --- YOUTUBE API CLIENT ---
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- YOUTUBE THEME CSS ---
def set_youtube_theme():
    st.markdown("""
    <style>
    body, .main, .reportview-container {
        background: #0e1117 !important;
        color: #fff !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #ff0000 !important; }
    .metric-card, .insight-card, .chart-container, .stDataFrame, .st-bb {
        background: #191c23 !important;
        color: #fff !important;
        border-radius: 10px !important;
        border-left: 4px solid #ff0000 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.16);
    }
    .metric-title, .insight-title {
        color: #ff7979 !important;
        font-size: 14px !important;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value, .insight-value { color: #fff !important; font-size: 28px !important; font-weight: 800; }
    .insight-card .insight-value { color: #ff0000 !important; }
    .stButton>button {
        border: none !important; background: #ff0000 !important; color: #fff !important; font-weight: bold !important;
        border-radius: 4px !important; padding: 8px 16px !important;
    }
    .stButton>button:hover { background: #cc0000 !important; }
    .stDataFrame { background: #191c23 !important; color: #fff !important; }
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label { color: #ff0000 !important; }
    .stRadio label { color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

set_youtube_theme()

# --- UTILITY FUNCTIONS ---
def format_number(num):
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def parse_duration(duration):
    try:
        if duration.startswith('PT'):
            duration = duration[2:]
            hours, minutes, seconds = 0, 0, 0
            if 'H' in duration:
                hours_part = duration.split('H')[0]
                hours = int(hours_part)
                duration = duration.split('H')[1]
            if 'M' in duration:
                minutes_part = duration.split('M')
                minutes = int(minutes_part)
                duration = duration.split('M')[1]
            if 'S' in duration:
                seconds_part = duration.split('S')
                seconds = int(seconds_part)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except:
        return 0

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

# --- API & DATA ---
@st.cache_data(ttl=3600, show_spinner="Fetching channel data...")
def get_channel_analytics(channel_id):
    try:
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails",
            id=channel_id
        ).execute()
        if not channel_response.get("items"):
            st.error("❌ Channel not found. Please check the Channel ID.")
            return None
        channel_info = channel_response["items"][0]

        # Get channel videos (limit 500)
        videos, next_page_token = [], None
        for _ in range(10):
            videos_response = youtube.search().list(
                channelId=channel_id,
                type="video",
                part="id,snippet",
                maxResults=50,
                order="date",
                pageToken=next_page_token
            ).execute()
            video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]
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

        for video in videos:
            video["engagement"] = ((video["likes"] + video["comments"]) / max(1, video["views"])) * 100

        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country", "N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"]
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

def calculate_earnings(videos_data, currency="USD", cpm_range="medium"):
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
    total_views = sum(video["views"] for video in videos_data)
    monthly_data = {}
    for video in videos_data:
        try:
            month = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {"views": 0, "videos": 0, "estimated_earnings": 0}
            monthly_data[month]["views"] += video["views"]
            monthly_data[month]["videos"] += 1
        except:
            continue
    for month in monthly_data:
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

# --- CHARTS ---
def chart_views_over_time(df):
    df['date'] = pd.to_datetime(df['published_at'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    monthly = df.groupby('month')['views'].sum().reset_index()
    fig = px.line(monthly, x='month', y='views', markers=True, title="Views Over Time",
                  labels={"views": "Views", "month": "Month"},
                  color_discrete_sequence=["#ff0000"])
    fig.update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff")
    return fig

def chart_engagement_distribution(df):
    fig = px.histogram(df, x="engagement", nbins=20, title="Engagement Rate Distribution (%)",
                       color_discrete_sequence=["#ff0000"])
    fig.update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff")
    return fig

def chart_top_videos_bar(df):
    top10 = df.nlargest(10, "views")
    fig = px.bar(top10, x="title", y="views", title="Top 10 Videos by Views",
                 color="views", color_continuous_scale="reds")
    fig.update_layout(xaxis_tickangle=-45, plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff")
    return fig

def chart_uploads_trend(df):
    df['date'] = pd.to_datetime(df['published_at'])
    uploads = df.groupby(df['date'].dt.to_period('M')).size().reset_index(name='uploads')
    uploads['month'] = uploads['date'].astype(str)
    fig = px.line(uploads, x="month", y="uploads", markers=True, title="Uploads per Month",
                  color_discrete_sequence=["#ff0000"])
    fig.update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff")
    return fig

def chart_earnings(df):
    fig = go.Figure()
    # Bar: Monthly Earnings
    fig.add_trace(go.Bar(
        x=df['month'], y=df['earnings'], name='Monthly Earnings', marker_color='#ff4b4b', opacity=0.7
    ))
    # Line: Cumulative Earnings
    fig.add_trace(go.Scatter(
        x=df['month'], y=df['earnings'].cumsum(), mode='lines+markers',
        name='Cumulative Earnings', line=dict(color='white', width=3)
    ))
    fig.update_layout(
        title="Monthly & Cumulative Earnings",
        xaxis_title='Month', yaxis_title='Earnings',
        plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"
    )
    return fig

# --- MAIN DASHBOARD ---
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")

    # --- Controls ---
    col_input1, col_input2 = st.columns([6, 1])
    with col_input1:
        channel_id = st.text_input(
            "Enter YouTube Channel ID",
            placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA"
        )
    with col_input2:
        analyze_btn = st.button("🚀 Analyze Channel")

    if not analyze_btn:
        st.markdown(
            "<br><div style='color:#ff0000;font-weight:bold;font-size:18px'>Enter Channel ID and Press Analyze 🚀</div><br>",
            unsafe_allow_html=True
        )
        return
    if not channel_id:
        st.error("Please enter a valid YouTube Channel ID")
        st.stop()

    with st.spinner("Fetching and analyzing channel data..."):
        channel_data = get_channel_analytics(channel_id)

    if not channel_data:
        st.stop()

    # --- Data processing ---
    video_df = pd.DataFrame(channel_data["videos"])
    if video_df.empty:
        st.warning("No videos found on the channel.")
        st.stop()
    video_df["published_at"] = pd.to_datetime(video_df["published_at"])
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["engagement"] = video_df["engagement"].round(2)
    video_df["publish_day"] = video_df["published_at"].dt.day_name()
    video_df["duration_min"] = video_df["duration_sec"] / 60

    # --- FILTERS ---
    st.sidebar.title("🔎 Filters")
    date_min, date_max = video_df["published_at"].min(), video_df["published_at"].max()
    date_range = st.sidebar.date_input(
        "Publish Date Range:",
        [date_min.date(), date_max.date()],
        min_value=date_min.date(),
        max_value=date_max.date()
    )
    min_views = st.sidebar.slider(
        "Minimum Views:", min_value=0, max_value=int(video_df["views"].max()), value=0, step=1000
    )
    min_engagement = st.sidebar.slider(
        "Minimum Engagement (%):", min_value=0.0, max_value=float(video_df["engagement"].max()), value=0.0, step=0.5
    )
    duration_filter = st.sidebar.selectbox(
        "Duration (minutes):", ["All", "<5", "5-10", "10-20", "20-60", "60+"]
    )
    currency = st.sidebar.selectbox("Currency:", ["USD", "INR", "EUR"])
    cpm_range = st.sidebar.selectbox("CPM/RPM Range:", ["low", "medium", "high"])

    # --- Apply filters ---
    df = video_df.copy()
    df = df[(df["published_at"].dt.date >= date_range[0]) & (df["published_at"].dt.date <= date_range[1])]
    df = df[df["views"] >= min_views]
    df = df[df["engagement"] >= min_engagement]
    if duration_filter != "All":
        if duration_filter == "<5":
            df = df[df["duration_min"] < 5]
        elif duration_filter == "5-10":
            df = df[(df["duration_min"] >= 5) & (df["duration_min"] < 10)]
        elif duration_filter == "10-20":
            df = df[(df["duration_min"] >= 10) & (df["duration_min"] < 20)]
        elif duration_filter == "20-60":
            df = df[(df["duration_min"] >= 20) & (df["duration_min"] < 60)]
        elif duration_filter == "60+":
            df = df[df["duration_min"] >= 60]

    # --- EARNINGS DATA ---
    earnings_data = calculate_earnings(df.to_dict(orient="records"), currency=currency, cpm_range=cpm_range)
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

    # --- CHANNEL HEADER ---
    col_header1, col_header2 = st.columns([1, 3])
    with col_header1:
        st.image(channel_data["basic_info"]["thumbnail"], width=100)
    with col_header2:
        st.markdown(f"## {channel_data['basic_info']['title']}")
        st.markdown(f"**Country**: {channel_data['basic_info']['country']}")
        st.markdown(f"**Channel ID**: {channel_id}")
        st.markdown(f"**Created**: {pd.to_datetime(channel_data['basic_info']['published_at']).strftime('%b %d, %Y')}")

    st.markdown("---")

    # --- KEY METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Subscribers", format_number(channel_data['statistics']['subscriber_count']))
    col2.metric("Total Views", format_number(channel_data['statistics']['view_count']))
    col3.metric("Total Videos", format_number(channel_data['statistics']['video_count']))

    st.markdown("---")

    # --- INSIGHTS CARDS ---
    st.subheader("🔍 Top Insights")
    ins_col1, ins_col2, ins_col3 = st.columns(3)
    # Best Performing Video
    if not df.empty:
        top_video = df.iloc[0]
        ins_col1.markdown(f"<div class='insight-card'><div class='insight-title'>Best Performing Video</div><div class='insight-value'>{format_number(top_video['views'])}</div><div>{top_video['title'][:50]}</div></div>", unsafe_allow_html=True)
    # Optimal Video Duration
    bins = [0, 5, 10, 20, 60, float('inf')]
    labels = ["<5m", "5-10m", "10-20m", "20-60m", "60m+"]
    df["duration_bin"] = pd.cut(df["duration_min"], bins=bins, labels=labels)
    if not df.empty:
        optimal_bin = df.groupby("duration_bin")["views"].mean().idxmax()
        ins_col2.markdown(f"<div class='insight-card'><div class='insight-title'>Optimal Video Length</div><div class='insight-value'>{optimal_bin}</div></div>", unsafe_allow_html=True)
    # Best Publish Day
    if not df.empty:
        best_day = df.groupby('publish_day')['views'].mean().idxmax()
        ins_col3.markdown(f"<div class='insight-card'><div class='insight-title'>Best Day to Publish</div><div class='insight-value'>{best_day}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- UNIQUE CHARTS ---
    chart1, chart2 = st.columns(2)
    chart1.plotly_chart(chart_views_over_time(df), use_container_width=True)
    chart2.plotly_chart(chart_top_videos_bar(df), use_container_width=True)

    chart3, chart4 = st.columns(2)
    chart3.plotly_chart(chart_engagement_distribution(df), use_container_width=True)
    chart4.plotly_chart(chart_uploads_trend(df), use_container_width=True)

    if not earnings_df.empty:
        st.plotly_chart(chart_earnings(earnings_df), use_container_width=True)

    st.markdown("---")

    # --- VIDEO PERFORMANCE TABLE ---
    st.subheader("🎥 Video Performance Table")
    sort_by = st.selectbox("Sort By:", ["views", "likes", "comments", "engagement", "published_at"])
    ascending = st.radio("Order:", ["Descending", "Ascending"]) == "Ascending"
    rows = st.slider("Rows to Display", min_value=5, max_value=40, value=10, step=5)
    sorted_df = df.sort_values(by=sort_by, ascending=ascending)
    st.dataframe(
        sorted_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]].head(rows),
        use_container_width=True
    )

youtube_dashboard()
