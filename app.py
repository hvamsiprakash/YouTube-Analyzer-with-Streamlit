import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIG & THEME ---
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM" # <- PUT YOUR API KEY HERE

st.set_page_config(page_title="YouTube Pro Analytics", layout="wide")
def set_youtube_theme():
    st.markdown("""
    <style>
    body, .main, .reportview-container { background: #0e1117 !important; color: #fff !important; }
    h1, h2, h3, h4, h5, .markdown-text-container { color: #fff !important; }
    label, .stSelectbox label, .stSlider label, .stDateInput label, .stTextInput label, .stRadio label { color:white !important; }
    .stButton>button { border:none !important; background:#ff0000 !important; color:#fff !important; font-weight:bold !important; border-radius:4px !important;}
    .stDataFrame td, .stDataFrame th { color:#fff !important; background:#191c23 !important;}
    .metric-card {background: #191c23 !important; color: #fff !important; border-radius:10px !important; 
    margin-bottom:24px !important; padding:15px !important; box-shadow: 0 4px 16px rgba(0,0,0,0.27);}
    </style>
    """, unsafe_allow_html=True)
set_youtube_theme()

# --- UTILS ---
def format_number(num):
    if num is None or pd.isna(num): return "N/A"
    if num >= 1_000_000_000: return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000: return f"{num/1_000_000:.1f}M"
    elif num >= 1_000: return f"{num/1_000:.1f}K"
    return str(num)

def parse_duration(duration_str):
    try:
        if not isinstance(duration_str, str) or not duration_str.startswith("PT"): return 0
        import re
        match = re.match("PT((\d+)H)?((\d+)M)?((\d+)S)?", duration_str)
        hours = int(match.group(2)) if match.group(2) else 0
        minutes = int(match.group(4)) if match.group(4) else 0
        seconds = int(match.group(6)) if match.group(6) else 0
        return hours*3600 + minutes*60 + seconds
    except: return 0

def format_duration(seconds):
    try:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0: return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    except: return "N/A"

@st.cache_data(ttl=3600)
def get_channel_data(channel_id):
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        res = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
        if not res.get("items"): return {"error": "Channel not found"}
        info = res["items"][0]

        videos, next_token = [], None
        for i in range(7): # 7*50=350 videos
            resp = youtube.search().list(channelId=channel_id, type="video", part="id,snippet", maxResults=50, order="date", pageToken=next_token).execute()
            vids = [v["id"].get("videoId") for v in resp.get("items",[])]
            if not vids: continue
            vinfo = youtube.videos().list(id=",".join(vids), part="statistics,snippet,contentDetails").execute()
            for vid in vinfo.get("items",[]):
                s, sn, dtl = vid.get("statistics",{}), vid.get("snippet",{}), vid.get("contentDetails",{})
                videos.append({
                    "title": sn.get("title",""),
                    "video_id": vid.get("id",""),
                    "published_at": sn.get("publishedAt",""),
                    "duration": dtl.get("duration"),
                    "views": int(s.get("viewCount",0)),
                    "likes": int(s.get("likeCount",0)),
                    "comments": int(s.get("commentCount",0)),
                })
            next_token = resp.get("nextPageToken")
            if not next_token: break
        return {
            "info": {
                "title": info["snippet"]["title"],
                "desc": info["snippet"].get("description",""),
                "thumb": info["snippet"]["thumbnails"]["high"]["url"],
                "country": info["snippet"].get("country",""),
                "created": info["snippet"]["publishedAt"]
            },
            "stats": {
                "views": int(info["statistics"].get("viewCount",0)),
                "subs": int(info["statistics"].get("subscriberCount",0)),
                "videos": int(info["statistics"].get("videoCount",0)),
            },
            "videos": videos
        }
    except Exception as e:
        return {"error":str(e)}

# --- DASHBOARD ---
st.title("🎬 YouTube Pro Analytics Dashboard")
channel_id = st.text_input("Enter YouTube Channel ID", placeholder="UCX6OQ3DkcsbYNE6H8uQQuVA")
go_btn = st.button("🚀 Analyze", use_container_width=True)
if not go_btn or not channel_id: st.stop()
data = get_channel_data(channel_id)
if "error" in data:
    st.error(f"❌ Error: {data['error']}")
    st.stop()
info, stats, videos = data["info"], data["stats"], data["videos"]
if not videos:
    st.warning("No videos found for this channel.")
    st.stop()
df = pd.DataFrame(videos)
df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
df["duration_sec"] = df["duration"].apply(parse_duration)
df["duration_min"] = df["duration_sec"] / 60
df["engagement"] = ((df["likes"]+df["comments"])/df["views"]).fillna(0)*100
df["publish_day"] = df["published_at"].dt.day_name()
df["publish_hour"] = df["published_at"].dt.hour

# --- FILTERS ---
with st.sidebar:
    st.write("## Filters")
    mind, maxd = df["published_at"].min(), df["published_at"].max()
    dr = st.date_input("Date range", [mind.date(), maxd.date()])
    vmin = st.slider("Min Views", 0, int(df["views"].max()), 0, 1000)
    emin = st.slider("Min Engagement (%)", 0.0, float(df["engagement"].max()), 0.0, 0.5)
    durbin = st.selectbox("Duration (min)", ["All", "<5", "5-10", "10-20", "20-60", "60+"])
dff = df.copy()
dff = dff[(dff["published_at"].dt.date >= dr[0]) & (dff["published_at"].dt.date <= dr[1])]
dff = dff[dff["views"] >= vmin]
dff = dff[dff["engagement"] >= emin]
if durbin!="All":
    if durbin=="<5": dff=dff[dff["duration_min"]<5]
    elif durbin=="5-10": dff=dff[(dff["duration_min"]>=5)&(dff["duration_min"]<10)]
    elif durbin=="10-20": dff=dff[(dff["duration_min"]>=10)&(dff["duration_min"]<20)]
    elif durbin=="20-60": dff=dff[(dff["duration_min"]>=20)&(dff["duration_min"]<60)]
    elif durbin=="60+": dff=dff[dff["duration_min"]>=60]

# --- CHANNEL HEADER ---
c1, c2 = st.columns([1,3])
with c1: st.image(info["thumb"], width=120)
with c2:
    st.markdown(f"### {info['title']}")
    st.write("- Country:", info["country"])
    st.write("- Created:", pd.to_datetime(info["created"]).strftime("%b %d, %Y"))
    st.write("- Total Views:", format_number(stats["views"]))
    st.write("- Subscribers:", format_number(stats["subs"]))
    st.write("- Video Count:", stats["videos"])
st.markdown("---")

# --- KEY CARDS ---
cardcols = st.columns(4)
def card(title, value, subval=None):
    cardcols[card.i].markdown(
        f"<div class='metric-card'><div style='font-size:16px;font-weight:600;color:#fff'>{title}</div>"
        f"<div style='font-size:24px;font-weight:800;color:#ff0000'>{value}</div>"
        f"<div style='font-size:13px;color:#fff'>{subval or ''}</div></div>", unsafe_allow_html=True
    )
    card.i = (card.i+1)%4
card.i = 0
card("Total Views", format_number(dff["views"].sum()))
card("Total Likes", format_number(dff["likes"].sum()))
card("Total Comments", format_number(dff["comments"].sum()))
card("Avg Engagement (%)", f"{dff['engagement'].mean():.2f}")
card("Avg Duration", f"{dff['duration_min'].mean():.1f} min")
card("Most Engaging Video", dff.iloc[dff["engagement"].idxmax()]["title"] if not dff.empty else "N/A")
card("Most Viewed Video", dff.iloc[dff["views"].idxmax()]["title"] if not dff.empty else "N/A")
if len(dff)>1: card("Upload Interval", f"{dff['published_at'].diff().dt.days.mean():.2f} days")
card("Upload Hour", dff["publish_hour"].mode()[0] if not dff.empty else "N/A")
card("Upload Day", dff["publish_day"].mode() if not dff.empty else "N/A")
st.markdown("---")

# --- 15 Graphs & Tables, all in white labels, red lines/bars ---
g1,g2 = st.columns(2)
g1.plotly_chart(
    px.line(dff.groupby(dff["published_at"].dt.date)["views"].sum().reset_index(),
            x="published_at", y="views", title="Views Over Time", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g2.plotly_chart(
    px.line(dff.groupby(dff["published_at"].dt.date)["likes"].sum().reset_index(),
            x="published_at", y="likes", title="Likes Over Time", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g3,g4 = st.columns(2)
g3.plotly_chart(
    px.line(dff.groupby(dff["published_at"].dt.date)["comments"].sum().reset_index(),
            x="published_at", y="comments", title="Comments Over Time", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g4.plotly_chart(
    px.histogram(dff, x="engagement", nbins=30, title="Engagement Rate Distribution (%)", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g5,g6 = st.columns(2)
g5.plotly_chart(
    px.scatter(dff, x="views", y="likes", title="Views vs Likes", color="likes", color_continuous_scale="reds")
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g6.plotly_chart(
    px.scatter(dff, x="views", y="comments", title="Views vs Comments", color="comments", color_continuous_scale="reds")
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g7,g8 = st.columns(2)
g7.plotly_chart(
    px.histogram(dff, x="duration_min", nbins=20, title="Video Duration Distribution (min)", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
if len(dff)>1:
    dff["days_since_last"] = dff["published_at"].diff().dt.days
    g8.plotly_chart(
        px.box(dff.dropna(), y="days_since_last", title="Interval Between Uploads (days)", color_discrete_sequence=["#ff0000"])
        .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g9,g10 = st.columns(2)
bins = [0,5,10,20,60,float('inf')]
labels = ["<5m","5-10m","10-20m","20-60m","60m+"]
dff["duration_bin"] = pd.cut(dff["duration_min"], bins=bins, labels=labels)
g9.plotly_chart(
    px.box(dff, x="duration_bin", y="views", title="Views by Duration Bin", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g10.plotly_chart(
    px.box(dff, x="duration_bin", y="likes", title="Likes by Duration Bin", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g11,g12 = st.columns(2)
g11.plotly_chart(
    px.box(dff, x="duration_bin", y="comments", title="Comments by Duration Bin", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
hours_data = dff.groupby("publish_hour").size().reset_index(name="count")
g12.plotly_chart(
    px.bar(hours_data, x="publish_hour", y="count", title="Popular Upload Hours", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
g13,g14 = st.columns(2)
days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
days_data = dff.groupby("publish_day").size().reindex(days_order, fill_value=0).reset_index(name="count").rename(columns={"index":"publish_day"})
g13.plotly_chart(
    px.bar(days_data, x="publish_day", y="count", title="Popular Upload Days", color_discrete_sequence=["#ff0000"])
    .update_layout(plot_bgcolor="#191c23", paper_bgcolor="#0e1117", font_color="#fff"), use_container_width=True)
# --- Tables ---
st.markdown("### Most Viewed Videos")
st.dataframe(
    dff.nlargest(10, "views")[["title", "views", "likes", "comments", "engagement", "duration_min"]],
    use_container_width=True
)
st.markdown("### Most Engaging Videos")
st.dataframe(
    dff.nlargest(10, "engagement")[["title", "views", "likes", "comments", "engagement", "duration_min"]],
    use_container_width=True
)
