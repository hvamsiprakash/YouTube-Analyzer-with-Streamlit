import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import isodate

API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig" # Replace with your YouTube API key

st.set_page_config(page_title="Advanced YouTube BI Dashboard", layout="wide", page_icon="🎥")

st.markdown("""
    <style>
    .stApp { background-color: #000 !important; color: #fff; }
    h1, h2, h3, h4, h5, h6, .stMarkdown { color: #fff !important; }
    [data-testid="stSidebar"] { background-color: #111 !important; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: white; }
    .stDataFrame td { color: white !important; }
    </style>
""", unsafe_allow_html=True)

red_palette = ['#ff0000','#d70000','#c60000','#b70000','#9b0000']

# --- API helpers
def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

@st.cache_data(ttl=1800)
def fetch_channel(channel_id):
    yt = get_youtube_client()
    req = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id)
    res = req.execute()
    if res["items"]:
        return res["items"][0]
    return None

@st.cache_data(ttl=1800)
def fetch_all_videos(uploads_playlist_id, max_results=300):
    yt = get_youtube_client()
    videos, nextPageToken = [], None
    while len(videos) < max_results:
        req = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=nextPageToken
        )
        res = req.execute()
        videos += res["items"]
        nextPageToken = res.get("nextPageToken")
        if not nextPageToken:
            break
    return [item["contentDetails"]["videoId"] for item in videos]

@st.cache_data(ttl=1800)
def fetch_video_details(video_ids):
    if not video_ids: return pd.DataFrame()
    yt = get_youtube_client()
    all_video = []
    for start in range(0, len(video_ids), 50):
        req = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids[start:start+50])
        )
        res = req.execute()
        for item in res["items"]:
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            all_video.append({
                "Video ID": item["id"],
                "Title": snippet.get("title", ""),
                "PublishedAt": snippet.get("publishedAt", ""),
                "Views": int(stats.get("viewCount", 0)),
                "Likes": int(stats.get("likeCount", 0)),
                "Comments": int(stats.get("commentCount", 0)),
                "Tags": snippet.get("tags", []),
                "CategoryId": snippet.get("categoryId", ""),
                "Duration": content.get("duration", "")
            })
    return pd.DataFrame(all_video)

@st.cache_data(ttl=1800)
def fetch_playlists(channel_id):
    yt = get_youtube_client()
    playlists, nextPageToken = [], None
    while True:
        req = yt.playlists().list(part="snippet,contentDetails", channelId=channel_id, maxResults=50, pageToken=nextPageToken)
        res = req.execute()
        playlists.extend(res["items"])
        nextPageToken = res.get("nextPageToken")
        if not nextPageToken:
            break
    return playlists

def parse_duration(duration):
    try:
        td = isodate.parse_duration(duration)
        return td.total_seconds() / 60  # minutes
    except:
        return 0

category_map = {
    "1": "Film", "2": "Autos", "10": "Music", "17": "Sports", "20": "Gaming", "23": "Comedy",
    "24": "Entertainment", "25": "News", "26": "Howto", "27": "Education", "28": "Science"
}

st.sidebar.title("📡 Channel Input")
channel_id = st.sidebar.text_input("Paste YouTube Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("❌ Channel not found.")
    else:
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        df["DurationMin"] = df["Duration"].map(parse_duration)
        df["PublishedDate"] = pd.to_datetime(df["PublishedAt"], errors='coerce')
        df["Month"] = df["PublishedDate"].dt.strftime("%Y-%m")
        df["DayOfWeek"] = df["PublishedDate"].dt.day_name()
        df["Year"] = df["PublishedDate"].dt.year
        df["Category"] = df["CategoryId"].map(lambda x: category_map.get(x, "Other"))
        df["CTR_Proxy"] = ((df["Likes"]+df["Comments"]) / df["Views"].replace(0, np.nan)).fillna(0)
        df["LikePerView"] = (df["Likes"] / df["Views"].replace(0, np.nan)).fillna(0)
        df["CommentPerView"] = (df["Comments"] / df["Views"].replace(0, np.nan)).fillna(0)

        # ---- Metric tiles
        st.markdown(f"<h2 style='color:#ff0000'>Advanced YouTube BI Dashboard — <span style='color:#fff'>{channel['snippet']['title']}</span></h2>",unsafe_allow_html=True)
        col_img, col_sub, col_views, col_vid, col_pl = st.columns([1,1,1,1,1])
        with col_img: st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=90)
        with col_sub: st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with col_views: st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with col_vid: st.metric("Videos", f"{int(channel['statistics']['videoCount']):,}")
        with col_pl: st.metric("Playlists", f"{len(playlists):,}")
        st.write("---")

        # --------- Sunburst: Category > Video > Likes ----------
        st.markdown("### 🌞 Engagement Sunburst (Category → Video → Comments)")
        sb_year = st.selectbox("Filter Sunburst Year", sorted(df["Year"].dropna().unique()))
        sub_df = df[df["Year"] == sb_year]
        sb_data = sub_df[["Category", "Title", "Comments"]]
        sb_data = sb_data[sb_data["Comments"] > 0]
        if not sb_data.empty:
            fig = px.sunburst(sb_data, path=["Category", "Title"], values="Comments",
                              color="Comments", color_continuous_scale=red_palette,
                              title="Comments Distribution (Sunburst)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No comments for selected year.")

        # --------- Treemap: Likes & Comments by Category ---------
        st.markdown("### 🍃 Engagement Treemap (Likes by Category)")
        tm_year = st.selectbox("Filter Treemap Year", sorted(df["Year"].dropna().unique()), key='tm_year')
        tm_df = df[df["Year"] == tm_year].groupby("Category")[["Likes","Comments"]].sum().reset_index()
        treemap_metric = st.radio("Treemap Metric", ["Likes","Comments"])
        fig = px.treemap(tm_df, path=["Category"], values=treemap_metric,
                         color=treemap_metric, color_continuous_scale=red_palette,
                         title=f"{treemap_metric} by Category")
        st.plotly_chart(fig, use_container_width=True)

        # --------- Radar Chart: Top 5 Videos Multi-Metrics ---------
        st.markdown("### 🕸 Radar Chart: Multi-Metric Comparison of Best Videos")
        top_count = st.slider("Number of Best Videos to Compare", 3, 10, 5)
        best_videos = df.sort_values("CTR_Proxy", ascending=False).head(top_count)
        radar_metrics = ["Views", "Likes", "Comments", "DurationMin", "CTR_Proxy"]
        categories = best_videos["Title"]
        radar_data = []
        for m in radar_metrics:
            radar_data.append(best_videos[m].values)
        fig = go.Figure()
        for i, row in best_videos.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row[met] for met in radar_metrics],
                theta=radar_metrics,
                fill='toself',
                name=row["Title"]
            ))
        fig.update_layout(
            polar=dict(bgcolor="#111", radialaxis=dict(visible=True, showticklabels=True)),
            showlegend=True,
            template=None,
            legend=dict(font=dict(color="white")),
            paper_bgcolor="#000",
            title="Radar: Top Videos by Multiple Metrics"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --------- Parallel Coordinates: Advanced Multi-Variable ---------
        st.markdown("### 🛣️ Parallel Coordinates: Multi-Variable Performance across Videos")
        pc_metrics = ["Views", "Likes", "Comments", "DurationMin", "CTR_Proxy"]
        pc_n = st.slider("Number of Videos (Parallel Coordinates)", 5, 50, 20)
        pc_df = df.sort_values("Views", ascending=False).head(pc_n)
        # Need numeric columns only, so ensure all pc_metrics exist and are numeric
        fig = px.parallel_coordinates(
            pc_df, dimensions=pc_metrics, color="Views",
            color_continuous_scale=red_palette, labels={m:m for m in pc_metrics},
            title="Parallel Coordinates: Video Performance"
        )
        st.plotly_chart(fig, use_container_width=True)
