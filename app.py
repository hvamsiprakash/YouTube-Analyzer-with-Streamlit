import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# ----- YOUTUBE API KEY -----
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"  # <-- Replace with your own API key!

# ----- THEME -----
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
    .stDataFrame td, .stDataFrame th { color:#fff !important; background:#191c23 !important;}
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label, .stRadio label { color: #ff0000 !important; }
    </style>
    """, unsafe_allow_html=True)

set_youtube_theme()

st.set_page_config(page_title="YouTube Pro Analytics", layout="wide")

# ----- FORMATTERS -----
def format_number(num):
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000: return f"{num/1_000_000:.1f}M"
    elif num >= 1_000: return f"{num/1_000:.1f}K"
    return str(num)

def parse_duration(duration):
    try:
        if not isinstance(duration, str): return 0
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
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0: return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else: return f"{minutes:02d}:{seconds:02d}"

# ----- API DATA -----
@st.cache_data(ttl=3600)
def get_channel_analytics(channel_id):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        # -- Channel Info --
        channel_response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()
        if not channel_response.get("items"):
            return {"error":"Not found"}

        channel_info = channel_response["items"][0]
        # -- Videos --
        videos, next_page_token = [], None
        for _ in range(10):
            videos_response = youtube.search().list(
                channelId=channel_id, type="video", part="id,snippet", maxResults=50, order="date", pageToken=next_page_token
            ).execute()
            video_ids = [item["id"].get("videoId") for item in videos_response.get("items", []) if item["id"].get("videoId")]
            if not video_ids: continue
            video_response = youtube.videos().list(
                part="statistics,snippet,contentDetails",
                id=",".join(video_ids)
            ).execute()
            for video in video_response.get("items", []):
                stats = video.get("statistics", {})
                snippet = video.get("snippet", {})
                details = video.get("contentDetails", {})
                videos.append({
                    "title": snippet.get("title", ""),
                    "video_id": video.get("id", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "duration": details.get("duration", ""),
                    "views": int(stats.get("viewCount",0)),
                    "likes": int(stats.get("likeCount",0)),
                    "comments": int(stats.get("commentCount",0))
                })
            next_page_token = videos_response.get("nextPageToken")
            if not next_page_token: break

        # Engagement
        for video in videos:
            v = video
            v["engagement"] = ((v["likes"]+v["comments"])/max(1,v["views"]))*100 if v["views"] else 0

        return {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"].get("description",""),
                "published_at": channel_info["snippet"].get("publishedAt",""),
                "country": channel_info["snippet"].get("country",""),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"]
            },
            "statistics": {
                "view_count": int(channel_info["statistics"].get("viewCount",0)),
                "subscriber_count": int(channel_info["statistics"].get("subscriberCount",0)),
                "video_count": int(channel_info["statistics"].get("videoCount",0)),
            },
            "videos": sorted(videos, key=lambda x: x["views"], reverse=True)
        }
    except Exception as e:
        return {"error":str(e)}

def calculate_earnings(videos_data, currency="USD", cpm_range="medium"):
    rpm_rates = {
        "USD": {"low": {"US": 1, "IN": 0.5, "other": 0.8}, "medium": {"US": 3, "IN": 1.5, "other": 2},
                "high": {"US": 5, "IN": 2.5, "other": 3.5}}
    }
    rates = rpm_rates.get(currency, rpm_rates["USD"])[cpm_range]
    total_views = sum(video["views"] for video in videos_data)
    monthly_data = {}
    for video in videos_data:
        try:
            month = pd.to_datetime(video["published_at"]).strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {"views":0,"videos":0,"estimated_earnings":0}
            monthly_data[month]["views"] += video["views"]
            monthly_data[month]["videos"] += 1
        except: continue
    for month in monthly_data:
        us_views = monthly_data[month]["views"] * 0.6
        in_views = monthly_data[month]["views"] * 0.1
        other_views = monthly_data[month]["views"] * 0.3
        us_earnings = (us_views / 1000) * rates["US"]
        in_earnings = (in_views / 1000) * rates["IN"]
        other_earnings = (other_views / 1000) * rates["other"]
        monthly_data[month]["estimated_earnings"] = us_earnings + in_earnings + other_earnings
    total_earnings = sum(month["estimated_earnings"] for month in monthly_data.values())
    return {
        "total_earnings": total_earnings,
        "monthly_earnings": monthly_data,
        "currency": currency,
        "cpm_range": cpm_range,
        "total_views": total_views,
        "estimated_rpm": total_earnings / (total_views/1000) if total_views else 0
    }

# ----- DASHBOARD -----
def youtube_dashboard():
    st.title("🎬 YouTube Pro Analytics Dashboard")

    col_input = st.columns([4,1])
    channel_id = col_input[0].text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    go_btn = col_input[1].button("🚀 Analyze")
    if not go_btn: st.stop()
    if not channel_id: st.error("Please enter a channel ID."); st.stop()
    result = get_channel_analytics(channel_id)
    if isinstance(result, dict) and result.get("error"):
        st.error(f"❌ Error fetching channel data: {result['error']}")
        st.stop()

    channel_data = result
    video_df = pd.DataFrame(channel_data["videos"])
    if video_df.empty: st.warning("No videos found on this channel."); st.stop()
    video_df["published_at"] = pd.to_datetime(video_df["published_at"], errors="coerce")
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["engagement"] = video_df["engagement"].round(2)
    video_df["duration_min"] = video_df["duration_sec"] / 60

    # SIDEBAR FILTERS
    st.sidebar.title("🔎 Filters")
    dmin, dmax = video_df["published_at"].min(), video_df["published_at"].max()
    date_range = st.sidebar.date_input("Publish Date Range", [dmin.date(), dmax.date()], min_value=dmin.date(), max_value=dmax.date())
    min_views = st.sidebar.slider("Minimum Views", min_value=0, max_value=int(video_df["views"].max()), value=0, step=1000)
    min_engagement = st.sidebar.slider("Minimum Engagement (%)", min_value=0.0, max_value=float(video_df["engagement"].max()), value=0.0, step=0.5)
    duration_filter = st.sidebar.selectbox("Duration (min)", ["All", "<5", "5-10", "10-20", "20-60", "60+"])
    currency = st.sidebar.selectbox("Currency", ["USD"])
    cpm_range = st.sidebar.selectbox("CPM/RPM Range", ["low", "medium", "high"])

    # APPLY FILTERS
    dff = video_df.copy()
    dff = dff[(dff["published_at"].dt.date >= date_range[0]) & (dff["published_at"].dt.date <= date_range[1])]
    dff = dff[dff["views"] >= min_views]
    dff = dff[dff["engagement"] >= min_engagement]
    if duration_filter != "All":
        if duration_filter == "<5": dff = dff[dff["duration_min"]<5]
        elif duration_filter == "5-10": dff = dff[(dff["duration_min"]>=5)&(dff["duration_min"]<10)]
        elif duration_filter == "10-20": dff = dff[(dff["duration_min"]>=10)&(dff["duration_min"]<20)]
        elif duration_filter == "20-60": dff = dff[(dff["duration_min"]>=20)&(dff["duration_min"]<60)]
        elif duration_filter == "60+": dff = dff[dff["duration_min"]>=60]

    # METRICS
    st.markdown("## Channel Summary")
    col_head = st.columns([1, 3])
    with col_head[0]: st.image(channel_data["basic_info"]["thumbnail"], width=100)
    with col_head[1]:
        st.markdown(f"### {channel_data['basic_info']['title']}")
        st.markdown(f"- **Country:** {channel_data['basic_info']['country']}")
        st.markdown(f"- **Channel ID:** `{channel_id}`")
        st.markdown(f"- **Created:** {pd.to_datetime(channel_data['basic_info']['published_at']).strftime('%b %d, %Y')}")
        st.markdown(f"- **Total Views:** {format_number(channel_data['statistics']['view_count'])}")
        st.markdown(f"- **Subscribers:** {format_number(channel_data['statistics']['subscriber_count'])}")
        st.markdown(f"- **Total Videos:** {format_number(channel_data['statistics']['video_count'])}")

    st.markdown("---")

    # Earnings
    earnings_data = calculate_earnings(dff.to_dict(orient="records"), currency=currency, cpm_range=cpm_range)
    monthly_earnings = []
    for month, data in earnings_data["monthly_earnings"].items():
        monthly_earnings.append({
            "month": month,
            "earnings": data["estimated_earnings"],
            "views": data["views"],
            "videos": data["videos"]
        })
    earnings_df = pd.DataFrame(monthly_earnings); earnings_df["month"] = pd.to_datetime(earnings_df["month"])

    # 8 Useful Insights
    st.subheader("🔍 Key Insights")
    i1 = format_number(dff["views"].sum())
    i2 = format_number(dff["likes"].sum())
    i3 = format_number(dff["comments"].sum())
    i4 = f"${earnings_data['total_earnings']:.2f}"
    i5 = f"${earnings_data['estimated_rpm']:.2f} RPM"
    i6 = f"{dff['engagement'].mean():.2f}% Avg Engagement"
    i7 = f"{dff['duration_min'].mean():.1f} min Avg Duration"
    if not dff.empty:
        top_video = dff.sort_values("engagement",ascending=False).iloc[0]
        i8 = f"Top Engagement: {top_video['title'][:50]}"
    else:
        i8 = "Top Engagement: N/A"

    ins_cols = st.columns(4)
    ins = [("Total Views",i1),("Total Likes",i2),("Total Comments",i3),("Total Earnings",i4),
           ("RPM (per 1k views)",i5),("Avg Engagement",i6),("Avg Duration",i7),("Highest Engagement Video",i8)]
    for idx, (t, v) in enumerate(ins): ins_cols[idx%4].markdown(f"<div class='insight-card'><div class='insight-title'>{t}</div><div class='insight-value'>{v}</div></div>",unsafe_allow_html=True)
    st.markdown("---")

    # CHARTS
    chart_cols = st.columns(2)
    # Views over time
    tv = dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["views"].sum().reset_index()
    chart_cols[0].plotly_chart(
        px.area(tv, x="published_at", y="views", title="Monthly Views Trend",color_discrete_sequence=["#ff0000"])
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Likes vs Comments
    chart_cols[1].plotly_chart(
        px.scatter(dff, x="likes", y="comments", title="Likes vs. Comments", color="views",color_continuous_scale="reds")
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # Earnings
    if not earnings_df.empty:
        st.plotly_chart(px.bar(earnings_df, x="month", y="earnings", title="Monthly Earnings",color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"), use_container_width=True)
    # Engagement Distribution
    st.plotly_chart(px.histogram(dff, x="engagement", nbins=20, title="Engagement Rate Distribution (%)",color_discrete_sequence=["#ff0000"])
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"), use_container_width=True)

    st.markdown("---")
    # Table
    st.subheader("🎥 Video Details Table")
    sort_by = st.selectbox("Sort By", ["views", "likes", "comments", "engagement", "published_at"])
    ascending = st.radio("Order", ["Descending", "Ascending"]) == "Ascending"
    rows = st.slider("Rows to Display", min_value=5, max_value=40, value=10, step=5)
    sorted_df = dff.sort_values(by=sort_by, ascending=ascending)
    st.dataframe(
        sorted_df[["title", "published_at", "views", "likes", "comments", "engagement", "duration_formatted"]].head(rows),
        use_container_width=True
    )

youtube_dashboard()
