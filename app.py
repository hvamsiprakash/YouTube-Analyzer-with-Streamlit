import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from datetime import datetime

YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"  # <- Replace with your own API key

# =========== THEME AND LAYOUT ===========
def set_youtube_theme():
    st.markdown("""
    <style>
    body, .main, .reportview-container { background: #0e1117 !important; color: #fff !important; }
    h1, h2, h3, h4, h5 { color: #fff !important; }
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label, .stRadio label { color:white !important; }
    .metric-card, .insight-card, .chart-container, .stDataFrame, .st-bb {
        background: #191c23 !important; color: #fff !important; border-radius:10px !important;
        margin-bottom:12px !important; padding:12px !important; box-shadow: 0 4px 16px rgba(0,0,0,0.27);
    }
    .insight-title { font-size: 15px !important; font-weight:700; color: #fff !important; margin-bottom:5px; }
    .insight-value { font-size: 24px !important; font-weight:800; color: #ff0000 !important;}
    .stButton>button { border:none !important; background:#ff0000 !important; color:#fff !important; font-weight:bold !important; border-radius:4px !important;}
    .stDataFrame td, .stDataFrame th { color:#fff !important; background:#191c23 !important;}
    .card-grid { display: flex; flex-wrap: wrap; gap:24px; margin-bottom:24px; }
    .insight-card { min-width:220px; flex:1; margin:8px; }
    </style>
    """, unsafe_allow_html=True)

set_youtube_theme()
st.set_page_config(page_title="YouTube Pro Analytics", layout="wide")

# =========== UTILS ===========
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

@st.cache_data(ttl=7200)
def get_channel_analytics(channel_id):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        channel_response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()
        if not channel_response.get("items"):
            return {"error":"Not found"}

        channel_info = channel_response["items"]
        videos, next_page_token = [], None
        for _ in range(10):
            videos_response = youtube.search().list(
                channelId=channel_id, type="video", part="id,snippet",
                maxResults=50, order="date", pageToken=next_page_token
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

# =========== DASHBOARD ===========
def youtube_dashboard():

    st.title("🎬 YouTube Pro Analytics Dashboard")
    channel_id = st.text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA", key="channel_id")
    go_btn = st.button("🚀 Analyze", key="go_btn")

    # Maintain session state so filters don't reset after submit
    if "data_loaded" not in st.session_state:
        st.session_state["data_loaded"] = False
    if go_btn and channel_id:
        st.session_state["channel_id"] = channel_id
        st.session_state["data_loaded"] = False
    if "channel_id" in st.session_state and not st.session_state["data_loaded"]:
        channel_id = st.session_state["channel_id"]
        with st.spinner("Fetching channel data..."):
            result = get_channel_analytics(channel_id)
            if isinstance(result, dict) and result.get("error"):
                st.error(f"❌ Error fetching data: {result['error']}")
                st.stop()
            st.session_state["channel_data"] = result
            st.session_state["data_loaded"] = True
    if "channel_data" not in st.session_state or not st.session_state["data_loaded"]:
        st.stop()

    channel_data = st.session_state["channel_data"]
    video_df = pd.DataFrame(channel_data["videos"])
    if video_df.empty: st.warning("No videos found."); st.stop()
    video_df["published_at"] = pd.to_datetime(video_df["published_at"], errors="coerce")
    video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
    video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
    video_df["engagement"] = video_df["engagement"].round(2)
    video_df["duration_min"] = video_df["duration_sec"] / 60
    video_df["publish_hour"] = video_df["published_at"].dt.hour
    video_df["publish_day"] = video_df["published_at"].dt.day_name()

    # ========== FILTERS ==========
    with st.sidebar:
        st.markdown("## Filters")
        dmin, dmax = video_df["published_at"].min(), video_df["published_at"].max()
        date_range = st.date_input("Publish Date Range", [dmin.date(), dmax.date()])
        min_views = st.slider("Minimum Views", min_value=0, max_value=int(video_df["views"].max()), value=0, step=1000)
        min_engage = st.slider("Min Engagement (%)", min_value=0.0, max_value=float(video_df["engagement"].max()), value=0.0, step=0.5)
        duration_filter_opt = st.selectbox("Duration (min)", ["All", "<5", "5-10", "10-20", "20-60", "60+"])

    dff = video_df.copy()
    dff = dff[(dff["published_at"].dt.date >= date_range[0]) & (dff["published_at"].dt.date <= date_range[1])]
    dff = dff[dff["views"] >= min_views]
    dff = dff[dff["engagement"] >= min_engage]
    if duration_filter_opt != "All":
        if duration_filter_opt == "<5": dff = dff[dff["duration_min"]<5]
        elif duration_filter_opt == "5-10": dff = dff[(dff["duration_min"]>=5)&(dff["duration_min"]<10)]
        elif duration_filter_opt == "10-20": dff = dff[(dff["duration_min"]>=10)&(dff["duration_min"]<20)]
        elif duration_filter_opt == "20-60": dff = dff[(dff["duration_min"]>=20)&(dff["duration_min"]<60)]
        elif duration_filter_opt == "60+": dff = dff[dff["duration_min"]>=60]

    # ========== CHANNEL HEADER SUMMARY ==========
    st.markdown("## Channel Summary")
    col_head = st.columns([1, 3])
    with col_head: st.image(channel_data["basic_info"]["thumbnail"], width=100)
    with col_head[1]:
        st.write(f"**{channel_data['basic_info']['title']}**")
        st.write(f"- Country: {channel_data['basic_info']['country']}")
        st.write(f"- Created: {pd.to_datetime(channel_data['basic_info']['published_at']).strftime('%B %d, %Y')}")
        st.write(f"- Channel ID: `{st.session_state['channel_id']}`")
        st.write(f"- Total Views: {format_number(channel_data['statistics']['view_count'])}")
        st.write(f"- Subscribers: {format_number(channel_data['statistics']['subscriber_count'])}")
        st.write(f"- Video Count: {format_number(channel_data['statistics']['video_count'])}")

    st.markdown("---")

    # ========== KEY INSIGHTS CARDS ==========
    st.markdown('<div class="card-grid">', unsafe_allow_html=True)
    insights = [
        ("Total Views", format_number(dff["views"].sum())),
        ("Total Likes", format_number(dff["likes"].sum())),
        ("Total Comments", format_number(dff["comments"].sum())),
        ("Avg Engagement (%)", f"{dff['engagement'].mean():.2f}"),
        ("Avg Duration (min)", f"{dff['duration_min'].mean():.1f}"),
        ("Most Engaging Video", dff.iloc[dff["engagement"].idxmax()]["title"] if not dff.empty else ""),
        ("Most Viewed Video", dff.iloc[dff["views"].idxmax()]["title"] if not dff.empty else ""),
        ("Upload Frequency (days)", f"{dff['published_at'].diff().dt.days.mean():.2f}" if len(dff)>1 else "N/A"),
        ("Popular Upload Hour", dff["publish_hour"].mode() if not dff.empty else "N/A"),
        ("Popular Upload Day", dff["publish_day"].mode() if not dff.empty else "N/A"),
    ]
    for title, value in insights:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ========== GRAPHS ==========
    st.markdown("## Channel Analytics")

    chart1, chart2 = st.columns(2)
    # 1. Views Over Time
    vtime = dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["views"].sum().reset_index()
    chart1.plotly_chart(
        px.line(vtime, x="published_at", y="views",
            title="Views Over Time", labels={"views":"Views","published_at":"Month"}, line_shape="spline",
            color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    # 2. Likes Over Time
    ltime = dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["likes"].sum().reset_index()
    chart2.plotly_chart(
        px.line(ltime, x="published_at", y="likes",
            title="Likes Over Time", labels={"likes":"Likes","published_at":"Month"}, line_shape="spline",
            color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    chart3, chart4 = st.columns(2)
    # 3. Comments Over Time
    ctime = dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["comments"].sum().reset_index()
    chart3.plotly_chart(
        px.line(ctime, x="published_at", y="comments", title="Comments Over Time",
            color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    # 4. Engagement Rate Distribution
    chart4.plotly_chart(
        px.histogram(dff, x="engagement", nbins=30, title="Engagement Rate Distribution (%)",
            color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    chart5, chart6 = st.columns(2)
    # 5. Views vs Likes
    chart5.plotly_chart(
        px.scatter(dff, x="views", y="likes", title="Views vs. Likes", color="likes", color_continuous_scale="reds")
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # 6. Views vs Comments
    chart6.plotly_chart(
        px.scatter(dff, x="views", y="comments", title="Views vs. Comments", color="comments", color_continuous_scale="reds")
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    chart7, chart8 = st.columns(2)
    # 7. Video Duration Distribution
    chart7.plotly_chart(
        px.histogram(dff, x="duration_min", nbins=20, title="Video Duration Distribution (min)",
            color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # 8. Upload Frequency (Days between uploads)
    if len(dff) > 1:
        dff["days_since_last"] = dff["published_at"].diff().dt.days
        chart8.plotly_chart(
            px.box(dff.dropna(), y="days_since_last", title="Interval Between Uploads (days)", color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
            use_container_width=True
        )

    chart9, chart10 = st.columns(2)
    # 9. Views by Duration Bin
    bins = [0,5,10,20,60,float('inf')]; labels=["<5m","5-10m","10-20m","20-60m","60m+"]
    dff["duration_bin"] = pd.cut(dff["duration_min"], bins=bins, labels=labels)
    chart9.plotly_chart(
        px.box(dff, x="duration_bin", y="views", title="Views by Duration Bin", color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )
    # 10. Likes by Duration Bin
    chart10.plotly_chart(
        px.box(dff, x="duration_bin", y="likes", title="Likes by Duration Bin", color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    chart11, chart12 = st.columns(2)
    # 11. Comments by Duration Bin
    chart11.plotly_chart(
        px.box(dff, x="duration_bin", y="comments", title="Comments by Duration Bin", color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
            use_container_width=True
    )
    # 12. Popular Upload Hours
    hours_data = dff.groupby("publish_hour").size().reset_index(name="count")
    chart12.plotly_chart(
        px.bar(hours_data, x="publish_hour", y="count", title="Popular Upload Hours", color_discrete_sequence=["#ff0000"])
        .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff"),
        use_container_width=True
    )

    chart13, chart14 = st.columns(2)
    # 13. Popular Upload Days
    days_data = dff.groupby("publish_day").size().reset_index(name="count")
    chart13.plotly_chart(
        px.bar(days_data, x="publish_day", y="count", title="Popular Upload Days", color_discrete_sequence=["#ff0000"])
            .update_layout(plot_bgcolor="#191c23",paper_bgcolor="#0e1117",font_color="#fff",
                           xaxis=dict(categoryorder="array",categoryarray=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])),
        use_container_width=True
    )
    # 14. Most Viewed Videos Table
    st.markdown("### Most Viewed Videos")
    st.dataframe(
        dff.nlargest(10, "views")[["title", "views", "likes", "comments", "engagement", "duration_formatted"]],
        use_container_width=True
    )
    # 15. Most Engaging Videos Table
    st.markdown("### Most Engaging Videos")
    st.dataframe(
        dff.nlargest(10, "engagement")[["title", "views", "likes", "comments", "engagement", "duration_formatted"]],
        use_container_width=True
    )

youtube_dashboard()

