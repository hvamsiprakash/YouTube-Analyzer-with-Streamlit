import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- YOUTUBE API KEY ---
YOUTUBE_API_KEY = "AIzaSyDGV_rw-styH4jKBMRr4fcX2-78jc79D3Q"

# --- THEME ---
def set_youtube_theme():
    st.markdown("""
    <style>
    body, .main, .reportview-container { background: #0e1117 !important; color: #fff !important; }
    h1, h2, h3, h4, h5 { color: #fff !important; }
    .metric-card, .insight-card, .chart-container, .stDataFrame, .st-bb {
        background: #191c23 !important; color: #fff !important;
        border-radius:10px !important; margin-bottom:15px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.27);  border: none !important;
    }
    .insight-title { color: #fff !important; font-size: 15px !important; font-weight: 700; margin-bottom:8px;}
    .insight-value { color: #fff !important; font-size: 22px !important; font-weight:700; margin-bottom:8px;}
    .insight-desc { color:#bbb !important; font-size:13px; margin-bottom:8px;}
    .insight-card { margin-right:24px !important; margin-top:8px !important; display:inline-block; vertical-align:top; width:230px;}
    .stButton>button { border:none !important; background:#ff0000 !important; color:#fff !important; font-weight:bold !important; border-radius:4px !important; }
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label, .stRadio label, .stCheckbox label { color: #fff !important; }
    .stDataFrame th, .stDataFrame td { color:#fff !important;}
    </style>
    """, unsafe_allow_html=True)
set_youtube_theme()
st.set_page_config(page_title="YouTube Pro Creator Dashboard", layout="wide")

# --- FORMATTERS ---
def format_number(val):
    if val is None: return ""
    if val >= 1_000_000_000: return f"{val/1_000_000_000:.1f}B"
    if val >= 1_000_000: return f"{val/1_000_000:.1f}M"
    if val >= 1_000: return f"{val/1_000:.1f}K"
    return str(val)

def parse_duration(dur):
    try:
        if not isinstance(dur, str): return 0
        if dur.startswith('PT'):
            dur = dur[2:]
            h, m, s = 0,0,0
            if 'H' in dur: h = int(dur.split('H')[0]); dur = dur.split('H')[1]
            if 'M' in dur: m = int(dur.split('M')); dur = dur.split('M')[1]
            if 'S' in dur: s = int(dur.split('S'))
            return h * 3600 + m * 60 + s
        return 0
    except: return 0

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = int(seconds % 60)
    if hours: return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

# --- API DATA (never cache UI controls) ---
@st.cache_data(ttl=1800)
def get_channel_data(channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    info = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
    if not info.get("items"):
        return {"error":"Channel not found."}
    ch = info["items"]
    videos = []; next_token=None
    for _ in range(10):
        vd = youtube.search().list(
            channelId=channel_id, type="video", part="id,snippet", maxResults=50, order="date", pageToken=next_token
        ).execute()
        ids = [i["id"]["videoId"] for i in vd.get("items",[]) if i["id"].get("videoId")]
        if not ids: continue
        vstat = youtube.videos().list(part="statistics,snippet,contentDetails", id=",".join(ids)).execute()
        for v in vstat.get("items",[]):
            sn, st, det = v.get("snippet",{}), v.get("statistics",{}), v.get("contentDetails",{})
            videos.append({
                "title": sn.get("title",""), "video_id": v.get("id",""), "published_at":sn.get("publishedAt",""),
                "duration":det.get("duration",""),
                "views":int(st.get("viewCount",0)), "likes":int(st.get("likeCount",0)), "comments":int(st.get("commentCount",0)),
                "thumbnail": sn.get("thumbnails",{}).get("high",{}).get("url",""),
            })
        next_token = vd.get("nextPageToken")
        if not next_token: break
    for v in videos:
        v["engagement"] = ((v["likes"]+v["comments"])/max(1,v["views"]))*100 if v["views"] else 0
    return {
        "basic_info":{
            "title":ch["snippet"]["title"], "description":ch["snippet"].get("description",""),
            "published_at":ch["snippet"].get("publishedAt",""), "country":ch["snippet"].get("country",""),
            "thumbnail":ch["snippet"]["thumbnails"]["high"]["url"]
        },
        "statistics":{
            "view_count": int(ch["statistics"].get("viewCount",0)), "subscriber_count":int(ch["statistics"].get("subscriberCount",0)),
            "video_count":int(ch["statistics"].get("videoCount",0)),
        },
        "videos":sorted(videos,key=lambda x:x["views"],reverse=True)
    }

# --- SESSION STATE ---
if "channel_id" not in st.session_state:
    st.session_state["channel_id"] = ""
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False
if "data" not in st.session_state:
    st.session_state["data"] = None

# --- HEADER ---
st.title("🎬 YouTube Pro Creator Dashboard")

if not st.session_state["data_loaded"]:
    st.session_state["channel_id"] = st.text_input(
        "Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
    analyze_btn = st.button("🚀 Analyze")
    if not analyze_btn:
        st.stop()
    if not st.session_state["channel_id"]:
        st.warning("Please enter a channel ID.")
        st.stop()
    res = get_channel_data(st.session_state["channel_id"])
    if res.get("error"):
        st.error(res["error"])
        st.stop()
    st.session_state["data"] = res
    st.session_state["data_loaded"] = True

channel_data = st.session_state["data"]
video_df = pd.DataFrame(channel_data["videos"])
video_df["published_at"] = pd.to_datetime(video_df["published_at"], errors="coerce")
video_df["duration_sec"] = video_df["duration"].apply(parse_duration)
video_df["duration_formatted"] = video_df["duration_sec"].apply(format_duration)
video_df["engagement"] = video_df["engagement"].round(2)
video_df["duration_min"] = video_df["duration_sec"] / 60

# --- SIDEBAR FILTERS (connected, persistently applied) ---
st.sidebar.title("🔎 Filters")
dmin, dmax = video_df["published_at"].min().date(), video_df["published_at"].max().date()
dates = st.sidebar.date_input("Date Range", [dmin, dmax], min_value=dmin, max_value=dmax)
min_views = st.sidebar.slider("Minimum Views", min_value=0, max_value=int(video_df["views"].max()), value=0, step=1000)
min_likes = st.sidebar.slider("Minimum Likes", min_value=0, max_value=int(video_df["likes"].max()), value=0, step=500)
duration_filter = st.sidebar.selectbox("Duration (min)", ["All", "<5", "5-10", "10-20", "20-60", "60+"])
st.sidebar.caption("All filter changes instantly apply below (no reset).")

dff = video_df.copy()
dff = dff[(dff["published_at"].dt.date >= dates[0]) & (dff["published_at"].dt.date <= dates[1])]
dff = dff[dff["views"] >= min_views]
dff = dff[dff["likes"] >= min_likes]
if duration_filter != "All":
    if duration_filter == "<5": dff = dff[dff["duration_min"]<5]
    elif duration_filter == "5-10": dff = dff[(dff["duration_min"]>=5)&(dff["duration_min"]<10)]
    elif duration_filter == "10-20": dff = dff[(dff["duration_min"]>=10)&(dff["duration_min"]<20)]
    elif duration_filter == "20-60": dff = dff[(dff["duration_min"]>=20)&(dff["duration_min"]<60)]
    elif duration_filter == "60+": dff = dff[dff["duration_min"]>=60]

# --- KEY INSIGHTS (spaced, white, dynamic, actionable) ---
st.markdown("## Key Insights")
insights = [
    {"title":"Total Views", "value":format_number(dff["views"].sum()), "desc":"Sum of all views for filtered videos."},
    {"title":"Subscribers", "value":format_number(channel_data["statistics"]["subscriber_count"]), "desc":"Current subscriber count."},
    {"title":"Total Likes", "value":format_number(dff["likes"].sum()), "desc":"Sum of likes."},
    {"title":"Total Comments", "value":format_number(dff["comments"].sum()), "desc":"Sum of comments."},
    {"title":"Avg Views/Video", "value":f"{dff['views'].mean():,.0f}", "desc":"Average views per video."},
    {"title":"Avg Likes/Video", "value":f"{dff['likes'].mean():,.0f}", "desc":"Average likes per video."},
    {"title":"Avg Comments/Video", "value":f"{dff['comments'].mean():,.0f}", "desc":"Average comments per video."},
    {"title":"Avg Engagement (%)", "value":f"{dff['engagement'].mean():.2f}", "desc":"Engagement: (likes+comments)/views."},
    {"title":"Upload Frequency (days)", "value":f"{dff['published_at'].diff().dt.days.mean():.1f}", "desc":"Mean days between uploads."},
    {"title":"Total Videos", "value":format_number(len(dff)), "desc":"Number of videos in filter."},
    {"title":"Longest Video", "value":f"{dff.sort_values('duration_sec',ascending=False)['duration_formatted'].iloc[0]}", "desc":dff.sort_values("duration_sec",ascending=False)["title"].iloc if not dff.empty else ""},
    {"title":"Shortest Video", "value":f"{dff.sort_values('duration_sec',ascending=True)['duration_formatted'].iloc}", "desc":dff.sort_values("duration_sec",ascending=True)["title"].iloc if not dff.empty else ""},
    {"title":"Top Engagement Video", "value":dff.loc[dff['engagement'].idxmax()]['title'][:32] if not dff.empty else "", "desc":"Highest engagement %."},
    {"title":"Most Viewed Video", "value":dff.loc[dff['views'].idxmax()]['title'][:32] if not dff.empty else "", "desc":"Highest views."},
    {"title":"Most Recent Video", "value":dff.sort_values('published_at',ascending=False)['title'].iloc[:32] if not dff.empty else "", "desc":"Latest post."},
]
for row_start in range(0, len(insights), 4):
    cols = st.columns(4)
    for i, card in enumerate(insights[row_start:row_start+4]):
        with cols[i]:
            st.markdown(f"""
            <div class='insight-card'>
                <div class='insight-title'>{card['title']}</div>
                <div class='insight-value'>{card['value']}</div>
                <div class='insight-desc'>{card['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
st.markdown('<br>', unsafe_allow_html=True)

# --- CHANNEL HEADER (white, left-aligned) ---
st.markdown(f"""
<div style='background:#191c23; border-radius:10px; padding:15px; margin-bottom:14px; color:#fff;'>
    <img src="{channel_data['basic_info']['thumbnail']}" width="85" style="float:left; margin-right:18px; border-radius:8px;">
    <span style="font-size:22px; font-weight:bold;">{channel_data['basic_info']['title']}</span><br>
    <span style="font-size:14px;">{channel_data['basic_info']['description']}</span><br>
    <span style="font-size:13px;">Country: {channel_data['basic_info']['country']}</span> ·
    <span style="font-size:13px;">Channel ID: {st.session_state['channel_id']}</span> ·
    <span style="font-size:13px;">Created: {pd.to_datetime(channel_data['basic_info']['published_at']).strftime('%b %d, %Y')}</span>
</div>
""", unsafe_allow_html=True)

# --- 15 UNIQUE GRAPHS/TABLES: ALL ACTIONABLE/WHITE LABELS, CHARTS IN RED ----
st.markdown("## Channel Analytics")

graph_sections = [
    ("Monthly Views Trend", px.area(dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["views"].sum().reset_index(),
        x="published_at", y="views", title="Monthly Views Trend", color_discrete_sequence=["#ff0000"])),
    ("Monthly Uploads", px.bar(dff.groupby(dff["published_at"].dt.strftime("%Y-%m")).size().reset_index(name="uploads"),
        x="published_at", y="uploads", title="Monthly Uploads", color_discrete_sequence=["#ff0000"])),
    ("Engagement Rate Distribution", px.histogram(dff, x="engagement", nbins=20, title="Engagement Rate (%)", color_discrete_sequence=["#ff0000"])),
    ("Views Distribution", px.histogram(dff, x="views", nbins=20, title="Views Distribution", color_discrete_sequence=["#ff0000"])),
    ("Likes vs Comments", px.scatter(dff, x="likes", y="comments", title="Likes vs Comments", color="views", color_continuous_scale="reds")),
    ("Views by Duration", px.box(dff, x=pd.cut(dff["duration_min"], bins=[0,5,10,20,60,120],labels=["<5","5-10","10-20","20-60","60+"]),
        y="views", title="Views by Video Duration", color_discrete_sequence=["#ff0000"])),
    ("Views By Day of Week", px.bar(dff.groupby(dff["published_at"].dt.day_name())["views"].sum().reset_index(),
        x="published_at", y="views", title="Views By Day", color_discrete_sequence=["#ff0000"])),
    ("Likes Heatmap", px.density_heatmap(dff, x="published_at", y="likes", title="Likes Over Time", color_continuous_scale="reds")),
    ("Comments Heatmap", px.density_heatmap(dff, x="published_at", y="comments", title="Comments Over Time", color_continuous_scale="reds")),
    ("Engagement Over Time", px.line(dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["engagement"].mean().reset_index(),
        x="published_at", y="engagement", title="Engagement Over Months", color_discrete_sequence=["#ff0000"])),
    ("Avg Duration Over Time", px.line(dff.groupby(dff["published_at"].dt.strftime("%Y-%m"))["duration_min"].mean().reset_index(),
        x="published_at", y="duration_min", title="Avg Duration Over Months", color_discrete_sequence=["#ff0000"])),
    ("Views Growth (Cumulative)", px.line(dff.sort_values("published_at").assign(cumu_views=dff.sort_values("published_at")["views"].cumsum()),
        x="published_at", y="cumu_views", title="Cumulative Views Growth", color_discrete_sequence=["#ff0000"])),
    ("Top 10 Videos Table", None), # Will do table below.
    ("Low Engagement Videos Table", None),
    ("Comments per Like Ratio", px.scatter(dff, x="likes", y="comments", size="views", color="engagement",
        title="Comments per Like, Sized by Views", color_continuous_scale="reds"))
]

for i in range(0, len(graph_sections)-2,2):
    cols = st.columns(2)
    # Left
    name, fig = graph_sections[i]
    if fig is not None:
        cols[0].plotly_chart(fig.update_layout(
            plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff",
            title=dict(text=name, font=dict(color="#fff",size=19)), margin=dict(t=45,b=30)), use_container_width=True)
    # Right
    name2, fig2 = graph_sections[i+1]
    if fig2 is not None:
        cols[1].plotly_chart(fig2.update_layout(
            plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff",
            title=dict(text=name2, font=dict(color="#fff",size=19)), margin=dict(t=45,b=30)), use_container_width=True)

# --- TABLES ---
st.markdown("### Top 10 Videos (by Views)")
top10 = dff.sort_values('views',ascending=False).head(10)[["title","published_at","views","likes","comments","engagement"]]
st.dataframe(top10,use_container_width=True)

st.markdown("### 10 Videos with Lowest Engagement (%)")
low_engage = dff.sort_values('engagement',ascending=True).head(10)[["title","published_at","views","likes","comments","engagement"]]
st.dataframe(low_engage,use_container_width=True)
