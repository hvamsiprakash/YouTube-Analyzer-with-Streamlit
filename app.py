import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

API_KEY = "AIzaSyDGV_rw-styH4jKBMRr4fcX2-78jc79D3Q"
BASE_URL = "https://www.googleapis.com/youtube/v3/"

st.set_page_config(page_title="YouTube Creator Dashboard", layout="wide")

# --- CUSTOM YOUTUBE THEME CSS ---
st.markdown("""
<style>
.stApp { background: #000000; color: #fff; }
h1, h2, h3, h4, h5, h6, p, div, span { color: #fff !important; }
[data-testid=stSidebar] { background: #121212 !important; }
.stTextInput input, .stSelectbox select, .stDateInput input { background: #282828 !important; color: #fff !important; border-color: #606060 !important; }
</style>
""", unsafe_allow_html=True)

# --- API DATA FETCHING FUNCTIONS ---

def fetch_channel_stats(channel_id):
    url = f"{BASE_URL}channels?part=snippet,statistics&id={channel_id}&key={API_KEY}"
    data = requests.get(url).json()
    if "items" in data and len(data["items"]) > 0:
        item = data["items"][0]
        return {
            "name": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "subscribers": int(item["statistics"].get("subscriberCount", 0)),
            "views": int(item["statistics"].get("viewCount", 0)),
            "videos": int(item["statistics"].get("videoCount", 0)),
            "join_date": item["snippet"]["publishedAt"][:10],
            "country": item["snippet"].get("country", ""),
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        }
    return None

def fetch_recent_videos(channel_id, max_results=20):
    url = f"{BASE_URL}search?part=snippet&channelId={channel_id}&maxResults={max_results}&order=date&type=video&key={API_KEY}"
    data = requests.get(url).json()
    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        published_at = item["snippet"]["publishedAt"]
        videos.append({"id": video_id, "title": title, "published_at": published_at})
    return pd.DataFrame(videos)

def fetch_video_stats(video_ids):
    results = []
    step = 50
    for i in range(0, len(video_ids), step):
        ids = ",".join(video_ids[i:i+step])
        url = f"{BASE_URL}videos?part=statistics,snippet&id={ids}&key={API_KEY}"
        data = requests.get(url).json()
        for item in data.get("items", []):
            stats = item["statistics"]
            snippet = item["snippet"]
            results.append({
                "id": item["id"],
                "title": snippet["title"],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "date": snippet["publishedAt"][:10]
            })
    return pd.DataFrame(results)

def fetch_comments(video_id, max_results=10):
    url = f"{BASE_URL}commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={API_KEY}"
    data = requests.get(url).json()
    comments = []
    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "text": snippet["textDisplay"],
            "author": snippet["authorDisplayName"],
            "time": snippet["publishedAt"][:10]
        })
    return comments

def fetch_channel_playlists(channel_id):
    url = f"{BASE_URL}playlists?part=snippet,contentDetails&channelId={channel_id}&maxResults=10&key={API_KEY}"
    data = requests.get(url).json()
    playlists = []
    for item in data.get("items", []):
        playlists.append({"title": item["snippet"]["title"], "count": int(item["contentDetails"].get("itemCount", 0))})
    return playlists

def fetch_competitors(query):
    url = f"{BASE_URL}search?part=snippet&type=channel&q={query}&maxResults=2&key={API_KEY}"
    data = requests.get(url).json()
    competitors = []
    for item in data.get("items", []):
        competitors.append({"id": item["id"]["channelId"], "name": item["snippet"]["title"]})
    return competitors

# --- SIDEBAR ---
with st.sidebar:
    st.header("Channel Config")
    channel_id = st.text_input("YouTube Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")
    show_top_videos = st.checkbox("Show Top 5 Videos by Views", value=True)
    show_views_trend = st.checkbox("Show Video Views Trend", value=True)
    show_playlists = st.checkbox("Show Playlists", value=True)
    show_comments = st.checkbox("Show Recent Comments", value=True)
    show_competitors = st.checkbox("Show Competitor Comparison", value=True)

# --- MAIN DASHBOARD ---
channel_data = fetch_channel_stats(channel_id)
if not channel_data:
    st.error("Invalid Channel ID or API error.")
    st.stop()
st.title(f"{channel_data['name']} – YouTube Creator Dashboard")
st.markdown(f"**Started:** {channel_data['join_date']} | **Country:** {channel_data['country']}")
st.image(channel_data['thumbnail'], width=100)
st.write(f"**Description:** {channel_data['description']}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Subscribers", f"{channel_data['subscribers']:,}")
col2.metric("Total Views", f"{channel_data['views']:,}")
col3.metric("Videos", f"{channel_data['videos']:,}")
channel_age = (datetime.now() - datetime.strptime(channel_data['join_date'], "%Y-%m-%d")).days // 365
col4.metric("Channel Age", f"{channel_age} yrs")

st.markdown("---")

# Fetch Recent Video Data
videos_df = fetch_recent_videos(channel_id, max_results=20)
if len(videos_df) == 0:
    st.warning("No public videos found.")
else:
    # Video Stats
    video_stats_df = fetch_video_stats(videos_df["id"].tolist())

    # Top 5 Videos by Views
    if show_top_videos and len(video_stats_df) > 0:
        st.subheader("Top 5 Videos by Views")
        top_videos = video_stats_df.nlargest(5, "views")[["title", "views"]]
        fig = px.bar(top_videos, x="views", y="title", orientation="h", color="views", title="Top 5 Videos",
                     color_continuous_scale=["red","#FF0000"])
        fig.update_layout(
            plot_bgcolor="#000", paper_bgcolor="#000", font=dict(color="white"),
            yaxis_title="", xaxis_title="Views"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Video Views Trend
    if show_views_trend and len(video_stats_df) > 0:
        st.subheader("Recent Video Views Trend")
        vtrend = video_stats_df.sort_values(by="date")
        fig = px.line(
            vtrend, x="date", y="views", title="Views Over Last 20 Uploads", markers=True,
            color_discrete_sequence=["#FF0000"]
        )
        fig.update_layout(
            plot_bgcolor="#000", paper_bgcolor="#000",
            font=dict(color="white"),
            xaxis_title="Upload Date", yaxis_title="Views"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Playlists
    if show_playlists:
        st.subheader("Channel Playlists")
        playlists = fetch_channel_playlists(channel_id)
        if playlists:
            df_playlists = pd.DataFrame(playlists)
            fig = px.bar(df_playlists, x="title", y="count", color="count",
                         color_continuous_scale=["#660000","#FF0000"], title="Videos per Playlist")
            fig.update_layout(plot_bgcolor="#000", paper_bgcolor="#000", font=dict(color="white"),
                             xaxis_title="Playlist", yaxis_title="Count", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No playlists found.")

    # Recent Comments (on latest video)
    if show_comments and len(video_stats_df) > 0:
        st.subheader("Recent Comments on Latest Video")
        comments = fetch_comments(video_stats_df.iloc[0]["id"], max_results=10)
        for c in comments:
            st.markdown(f"<div style='background:#181818;border-left:6px solid #FF0000;padding:6px 14px;margin-bottom:5px;color:white;border-radius:8px'><b>{c['author']}</b>: {c['text']} <br><span style='color:#AAAAAA'>{c['time']}</span></div>", unsafe_allow_html=True)

    # Competitor Comparison
    if show_competitors:
        st.subheader("Competitor Comparison (by name search)")
        competitors = fetch_competitors(channel_data["name"])
        comp_stats = []
        for comp in competitors:
            comp_data = fetch_channel_stats(comp["id"])
            if comp_data:
                comp_stats.append(comp_data)
        if comp_stats:
            comp_df = pd.DataFrame({
                "Metric": ["Subscribers", "Views", "Videos"],
                channel_data["name"]: [channel_data["subscribers"], channel_data["views"], channel_data["videos"]],
                comp_stats["name"]: [comp_stats["subscribers"], comp_stats["views"], comp_stats["videos"]],
                comp_stats["name"]: [comp_stats["subscribers"], comp_stats["views"], comp_stats["videos"]]
            })
            fig = px.bar(comp_df, x="Metric", y=comp_df.columns[1:], title="Competitor Comparison",
                        barmode="group", color_discrete_sequence=["#FF0000","#990000","#660000"])
            fig.update_layout(plot_bgcolor="#000", paper_bgcolor="#000", font=dict(color="white"),
                             xaxis_title="", yaxis_title="Value")
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align:center;color:#AAAAAA;'>Dashboard powered by YouTube Data API v3 • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
