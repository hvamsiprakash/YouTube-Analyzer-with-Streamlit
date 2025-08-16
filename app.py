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

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

st.set_page_config(page_title="YouTube Pro Analytics", layout="wide")

# --- THEME ---
def set_youtube_theme():
    st.markdown("""
    <style>
    body, .main, .reportview-container { background: #0e1117 !important; color: #fff !important; }
    h1, h2, h3, h4, h5 { color: #ff0000 !important; }
    .metric-card, .insight-card, .chart-container, .stDataFrame, .st-bb {
        background: #191c23 !important; color: #fff !important; border-radius:10px !important;
        border-left: 3px solid #ff0000 !important; box-shadow: 0 4px 16px rgba(0,0,0,0.27);
    }
    .metric-title, .insight-title { color: #ff7979 !important; font-size: 13px !important; font-weight: 700; }
    .metric-value, .insight-value { color:#fff !important; font-size:25px !important; font-weight:800;}
    .insight-card .insight-value { color: #ff0000 !important; }
    .stButton>button { border:none !important; background:#ff0000 !important; color:#fff !important; font-weight:bold !important; border-radius:4px !important; }
    .stDataFrame td { color:#fff !important; }
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label, .stRadio label { color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)
set_youtube_theme()

def format_number(num):
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000: return f"{num/1_000_000:.1f}M"
    elif num >= 1_000: return f"{num/1_000:.1f}K"
    return str(num)

def parse_duration(duration):
    try:
        if duration.startswith('PT'):
            duration = duration[2:]
            hours, minutes, seconds = 0,0,0
            if 'H' in duration: hours_part = duration.split('H')[0]; hours=int(hours_part); duration=duration.split('H')[1]
            if 'M' in duration: minutes_part=duration.split('M'); minutes=int(minutes_part); duration=duration.split('M')[1]
            if 'S' in duration: seconds_part=duration.split('S'); seconds=int(seconds_part)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except: return 0

def format_duration(seconds):
    hours = seconds // 3600; minutes = (seconds % 3600) // 60; seconds = seconds % 60
    if hours > 0: return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else: return f"{minutes:02d}:{seconds:02d}"

@st.cache_data(ttl=3600, show_spinner="Fetching channel data...")
def get_channel_analytics(channel_id):
    try:
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails",
            id=channel_id
        ).execute()
        if not channel_response.get("items"):
            st.error("❌ Channel not found.")
            return None
        channel_info = channel_response["items"]

        videos, next_page_token = [], None
        for _ in range(10):
            videos_response = youtube.search().list(
                channelId=channel_id, type="video", part="id,snippet",
                maxResults=50, order="date", pageToken=next_page_token
            ).execute()
            video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                video_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails",
                    id=",".join(batch_ids)
                ).execute()
                for video in video_response.get("items", []):
                    stats = video["statistics"]; snippet = video["snippet"]; details = video["contentDetails"]
                    videos.append({
                        "title": snippet.get("title","N/A"),
                        "video_id": video["id"],
                        "published_at": snippet.get("publishedAt","N/A"),
                        "duration": details.get("duration","PT0M"),
                        "views": int(stats.get("viewCount",0)),
                        "likes": int(stats.get("likeCount",0)),
                        "comments": int(stats.get("commentCount",0)),
                        "thumbnail": snippet.get("thumbnails",{}).get("high",{}).get("url","")
                    })
            next_page_token = videos_response.get("nextPageToken")
            if not next_page_token: break
        for video in videos:
            video["engagement"] = ((video["likes"]+video["comments"])/max(1,video["views"]))*100
        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country","N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"]
            },
            "statistics": {
                "view_count": int(channel_info["statistics"]["viewCount"]),
                "subscriber_count": int(channel_info["statistics"]["subscriberCount"]),
                "video_count": int(channel_info["statistics"]["videoCount"]),
            },
            "videos": sorted(videos, key=lambda x: x["views"], reverse=True)
        }
        return channel_data
    except Exception as e:
        st.error(f"❌ Error fetching channel data: {str(e)}")
        return None

def calculate_earnings(videos_data, currency="USD", cpm_range="medium"):
    rpm_rates = {
        "USD": {"low": {"US": 1, "IN": 0.5, "other": 0.8}, "medium": {"US": 3, "IN": 1.5, "other": 2},
                "high": {"US": 5, "IN": 2.5, "other": 3.5}},
        "INR": {"low": {"US": 80, "IN": 40, "other": 60}, "medium": {"US": 240, "IN": 120, "other": 160},
                "high": {"US": 400, "IN": 200, "other": 280}},
        "EUR": {"low": {"US": 0.9, "IN": 0.45, "other": 0.7}, "medium": {"US": 2.7, "IN": 1.35, "other": 1.8},
                "high": {"US": 4.5, "IN": 2.25, "other": 3.15}}
    }
    total_views = sum(video["views"] for video in videos_data)
    monthly_data = {}
    for video in videos_data:
        try:
            month = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {"views":0,"videos":0,"estimated_earnings":0}
            monthly_data[month]["views"] += video["views"];
            monthly_data[month]["videos"] += 1
        except: continue
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

# --- MAIN DASHBOARD ---
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")

    col_input1, col_input2 = st.columns([6,1])
    with col_input1:
        channel_id = st.text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    with col_input2:
        analyze_btn = st.button("🚀 Analyze Channel")
    if not analyze_btn: st.stop()
    if not channel_id:
        st.error("Please enter a valid YouTube Channel ID")
        st.stop()
    with st.spinner("Fetching and analyzing channel data..."):
        channel_data = get_channel_analytics(channel_id)
    if not channel_data: st.stop()

    video_df = pd.DataFrame(channel_data["videos"])
    if video_df.empty: st.warning("No videos found."); st.stop()
    video_df["published_at"] = pd.to_datetime(video_df["published_at"])
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["engagement"] = video_df["engagement"].round(2)
    video_df["publish_day"] = video_df["published_at"].dt.day_name()
    video_df["duration_min"] = video_df["duration_sec"] / 60

    # SIDEBAR FILTERS
    st.sidebar.title("🔎 Filters")
    date_min, date_max = video_df["published_at"].min(), video_df["published_at"].max()
    date_range = st.sidebar.date_input("Publish Date Range:", [date_min.date(), date_max.date()],
        min_value=date_min.date(), max_value=date_max.date())
    min_views = st.sidebar.slider("Minimum Views:", min_value=0, max_value=int(video_df["views"].max()), value=0, step=1000)
    min_engagement = st.sidebar.slider("Minimum Engagement (%):", min_value=0.0, max_value=float(video_df["engagement"].max()), value=0.0, step=0.5)
    duration_filter = st.sidebar.selectbox("Duration (minutes):", ["All", "<5", "5-10", "10-20", "20-60", "60+"])
    currency = st.sidebar.selectbox("Currency:", ["USD", "INR", "EUR"])
    cpm_range = st.sidebar.selectbox("CPM/RPM Range:", ["low", "medium", "high"])

    # FILTER
    df = video_df.copy()
    df = df[(df["published_at"].dt.date >= date_range[0]) & (df["published_at"].dt.date <= date_range[1])]
    df = df[df["views"] >= min_views]
    df = df[df["engagement"] >= min_engagement]
    if duration_filter != "All":
        if duration_filter=="<5": df=df[df["duration_min"]<5]
        elif duration_filter=="5-10": df=df[(df["duration_min"]>=5)&(df["duration_min"]<10)]
        elif duration_filter=="10-20": df=df[(df["duration_min"]>=10)&(df["duration_min"]<20)]
        elif duration_filter=="20-60": df=df[(df["duration_min"]>=20)&(df["duration_min"]<60)]
        elif duration_filter=="60+": df=df[df["duration_min"]>=60]

    # EARNINGS DATA
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
    earnings_df = pd.DataFrame(monthly_earnings); earnings_df["month"] = pd.to_datetime(earnings_df["month"])

    # CHANNEL HEADER METRICS
    st.markdown("## Channel Summary")
    col_head1, col_head2 = st.columns([1, 3])
    with col_head1: st.image(channel_data["basic_info"]["thumbnail"], width=100)
    with col_head2:
        st.markdown(f"### {channel_data['basic_info']['title']}")
        st.markdown(f"- **Country:** {channel_data['basic_info']['country']}")
        st.markdown(f"- **Channel ID:** `{channel_id}`")
        st.markdown(f"- **Created:** {pd.to_datetime(channel_data['basic_info']['published_at']).strftime('%b %d, %Y')}")
    st.markdown("---")

    # --- 20 INSIGHTS ---
    st.subheader("🔍 20 Useful Insights")
    # 1. Subscribers Growth (show delta if possible)
    # 2. Views Trend (show % change last vs previous period)
    recent_period_days = 30
    now = datetime.now(); past = now - timedelta(days=recent_period_days)
    df_recent = df[df["published_at"].dt.date >= past.date()]; df_older = df[df["published_at"].dt.date < past.date()]
    subscribers = channel_data['statistics']['subscriber_count']
    views_total = df["views"].sum(); views_recent = df_recent["views"].sum(); views_older = df_older["views"].sum()
    # 3. Estimated Earnings
    total_earnings = earnings_data['total_earnings']
    # 4. RPM (Revenue Per Mille)
    rpm = earnings_data['estimated_rpm']
    # 5. Total Comments
    total_comments = df["comments"].sum()
    # 6. Total Likes
    total_likes = df["likes"].sum()
    # 7. Engagement Over Time Mean
    eng_over_time = df.groupby(df["published_at"].dt.to_period("M"))["engagement"].mean()
    # 8. Top 5 Videos by Engagement
    top_engage = df.sort_values("engagement",ascending=False).head(5)
    # 9. Average Video Duration
    avg_vid_duration = df["duration_min"].mean()
    # 10. Optimal Duration Bin
    bins = [0,5,10,20,60,float('inf')]; labels=["<5m","5-10m","10-20m","20-60m","60m+"]
    df["duration_bin"] = pd.cut(df["duration_min"], bins=bins, labels=labels)
    optimal_bin = df.groupby("duration_bin")["views"].mean().idxmax()
    # 11. Average Views per Video
    avg_views = df["views"].mean()
    # 12. Average Likes per Video
    avg_likes = df["likes"].mean()
    # 13. Average Comments per Video
    avg_comments = df["comments"].mean()
    # 14. Upload Frequency (mean days between uploads)
    upload_freq = df["published_at"].diff().dt.days.mean()
    # 15. Views Distribution by Duration
    # 16. Likes vs Comments Correlation
    correlation = df[["likes","comments"]].corr().loc["likes","comments"]
    # 17. Highest Earning Video (estimate through RPM)
    df["earnings_est"] = (df["views"]/1000)*rpm
    highest_earning_video = df.sort_values("earnings_est",ascending=False).iloc[0]
    # 18. Views from Recent 5 Videos
    views_last_5 = df.sort_values("published_at",ascending=False).head(5)["views"].sum()
    # 19. Monthly Uploads Trend
    month_uploads = df.groupby(df["published_at"].dt.strftime("%Y-%m")).size()
    # 20. Total Watchtime Estimate (duration * views)
    df["watch_time_hours"] = (df["duration_sec"]*df["views"])/3600
    total_watchtime = df["watch_time_hours"].sum()

    # Insights Render
    insight_items = [
        ("Subscribers", format_number(subscribers)),
        ("Views (Filtered)", format_number(views_total)),
        ("Views Past 30 Days", format_number(views_recent)),
        ("Estimated Earnings", f"{format_number(total_earnings)} {currency}"),
        ("RPM (per 1k views)", f"{rpm:.2f} {currency}"),
        ("Total Likes", format_number(total_likes)),
        ("Total Comments", format_number(total_comments)),
        ("Avg Engagement (%)", f"{df['engagement'].mean():.2f}"),
        ("Avg Video Duration", f"{avg_vid_duration:.1f} min"),
        ("Optimal Duration (views)", str(optimal_bin)),
        ("Avg Views/Video", f"{avg_views:.0f}"),
        ("Avg Likes/Video", f"{avg_likes:.0f}"),
        ("Avg Comments/Video", f"{avg_comments:.0f}"),
        ("Upload Frequency (days)", f"{upload_freq:.1f}"),
        ("> 1k Likes Videos", f"{(df['likes']>1000).sum()}"),
        ("Top Engagement Video", top_engage['title'].iloc[:60]),
        ("Likes-Comments Correlation", f"{correlation:.2f}"),
        ("Highest Earning Video", highest_earning_video['title'][:60]),
        ("Views Recent 5 Videos", format_number(views_last_5)),
        ("Total Watch Time (hours)", f"{total_watchtime:,.0f}"),
    ]
    grid_cols = st.columns(4)
    for idx, (title, value) in enumerate(insight_items):
        with grid_cols[idx%4]:
            st.markdown(f"<div class='insight-card'><div class='insight-title'>{title}</div><div class='insight-value'>{value}</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- DYNAMIC GRAPHS ---
    st.subheader("📈 Dynamic Channel Charts")
    ch1, ch2 = st.columns(2)
    # Subscribers Growth (simulate as YouTube API does not expose per month, using video count as proxy trend)
    month_subs_df = pd.DataFrame({"Month":month_uploads.index, "Video Uploads":month_uploads.values})
    ch1.plotly_chart(
        px.bar(month_subs_df, x="Month", y="Video Uploads", title="Monthly Upload Count (Activity Proxy)",
            color_discrete_sequence=["#ff0000"]).update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Views Trend
    monthly_views = df.groupby(df["published_at"].dt.strftime("%Y-%m"))["views"].sum().reset_index()
    ch2.plotly_chart(
        px.line(monthly_views, x="published_at", y="views", markers=True, title="Monthly Views",
            labels={"published_at":"Month","views":"Views"},color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    ch3, ch4 = st.columns(2)
    # Earnings Trend
    if not earnings_df.empty:
        ch3.plotly_chart(
            px.bar(earnings_df, x="month", y="earnings", title="Monthly Earnings",
                color_discrete_sequence=["#ff0000"])
                .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
            use_container_width=True)
    # Engagement Over Time
    eng_month = df.groupby(df["published_at"].dt.strftime("%Y-%m"))["engagement"].mean().reset_index()
    ch4.plotly_chart(
        px.line(eng_month, x="published_at", y="engagement", markers=True, title="Avg Engagement (%) Over Time",
            color_discrete_sequence=["#ff7979"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Distribution Views by Duration
    st.plotly_chart(px.box(
        df, x="duration_bin", y="views", title="Views by Video Duration",
        color_discrete_sequence=["#ff0000"],labels={"duration_bin":"Duration Bin","views":"Views"})
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Top 5 Videos Engagement
    st.plotly_chart(px.bar(
        top_engage, x="title", y="engagement", title="Top 5 Videos by Engagement (%)",
        color="engagement",color_continuous_scale="reds")
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff",xaxis_tickangle=-30),
        use_container_width=True
    )
    # Likes vs Comments Correlation
    st.plotly_chart(px.scatter(
        df, x="likes", y="comments", title="Likes vs Comments (Correlation)",
        color="views",color_continuous_scale="reds",labels={"likes":"Likes","comments":"Comments"})
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Watchtime Histogram
    st.plotly_chart(px.histogram(
        df, x="watch_time_hours", nbins=20, title="Distribution of Watch Time (hours) per Video",
        color_discrete_sequence=["#ff0000"],labels={"watch_time_hours":"Watch Time (hours)"})
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    st.markdown("---")

    # --- VIDEO PERFORMANCE TABLE ---
    st.subheader("🎥 Video Performance Table")
    sort_by = st.selectbox("Sort By:", ["views", "likes", "comments", "engagement", "published_at","earnings_est"])
    ascending = st.radio("Order:", ["Descending", "Ascending"]) == "Ascending"
    rows = st.slider("Rows to Display", min_value=5, max_value=40, value=10, step=5)
    sorted_df = df.sort_values(by=sort_by, ascending=ascending)
    st.dataframe(
        sorted_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted", "earnings_est", "watch_time_hours"]].head(rows),
        use_container_width=True
    )

youtube_dashboard()
