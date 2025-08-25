import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import isodate

# ========================
# API CONFIG
# ========================
API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"  # Replace with your API key

st.set_page_config(
    page_title="YouTube Advanced BI Dashboard",
    layout="wide",
    page_icon="🎥"
)

# ========================
# THEME (POWERBI STYLE)
# ========================
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF; }
    h1, h2, h3, h4, h5, h6, .stMarkdown { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: white; }
    .stDataFrame td { color: white !important; }
    </style>
""", unsafe_allow_html=True)

red_palette = ['#ff0000','#d70000','#c60000','#b70000','#9b0000']

# ========================
# API HELPERS
# ========================
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
        return td.total_seconds() / 60  # in minutes
    except:
        return 0

category_map = {
    "1": "Film", "2": "Autos", "10": "Music", "17": "Sports", "20": "Gaming", "23": "Comedy",
    "24": "Entertainment", "25": "News", "26": "Howto", "27": "Education", "28": "Science"
}

# ========================
# DASHBOARD
# ========================
st.sidebar.title("📡 Channel Input")
channel_id = st.sidebar.text_input("Enter YouTube Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("❌ Channel not found.")
    else:
        st.title(f"📊 YouTube BI Dashboard — {channel['snippet']['title']}")
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        # --------------------
        # PREPROCESS
        # --------------------
        df["DurationMin"] = df["Duration"].map(parse_duration)
        df["PublishedDate"] = pd.to_datetime(df["PublishedAt"], errors="coerce")
        df["Month"] = df["PublishedDate"].dt.strftime("%Y-%m")
        df["DayOfWeek"] = df["PublishedDate"].dt.day_name()
        df["Hour"] = df["PublishedDate"].dt.hour
        df["Year"] = df["PublishedDate"].dt.year
        df["Category"] = df["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        # Ratios for CTR proxy & engagement
        df["CTR_Proxy"] = ((df["Likes"]+df["Comments"]) / df["Views"].replace(0, np.nan)).fillna(0)
        df["LikePerView"] = (df["Likes"] / df["Views"].replace(0, np.nan)).fillna(0)
        df["CommentPerView"] = (df["Comments"] / df["Views"].replace(0, np.nan)).fillna(0)
        df["LikePerMinute"] = (df["Likes"] / df["DurationMin"].replace(0, np.nan)).fillna(0)

        # --------------------
        # CHANNEL METRICS
        # --------------------
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=100)
        with c2: st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with c3: st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with c4: st.metric("Videos", f"{int(channel['statistics']['videoCount']):,}")
        with c5: st.metric("Playlists", f"{len(playlists):,}")

        st.write("---")

        # ========================
        # INSIGHTS
        # ========================

        # 1. Subscriber Growth Approximation
        st.markdown("### 📈 Subscriber Growth Trend (Approx)")
        subs_df = df.groupby("Month")["Views"].sum().reset_index()
        # distribute subscriber count over time ~ proportional to views
        total_views = subs_df["Views"].sum()
        subs_df["Subscribers"] = (subs_df["Views"] / total_views) * int(channel["statistics"]["subscriberCount"])
        subs_df["SubscribersCumulative"] = subs_df["Subscribers"].cumsum()
        fig = px.line(subs_df, x="Month", y="SubscribersCumulative", markers=True,
                      color_discrete_sequence=[red_palette[0]],
                      title="Estimated Subscriber Growth over Time")
        st.plotly_chart(fig, use_container_width=True)

        # 2. CTR Proxy over time
        st.markdown("### 🎯 CTR Proxy Trend (Likes+Comments per View)")
        ctr_trend = df.groupby("Month")["CTR_Proxy"].mean().reset_index()
        fig = px.area(ctr_trend, x="Month", y="CTR_Proxy", color_discrete_sequence=[red_palette[1]],
                      title="CTR Proxy (Avg per Month)")
        st.plotly_chart(fig, use_container_width=True)

        # 3. Engagement by Category
        st.markdown("### 🗂 Engagement by Category")
        cat_df = df.groupby("Category")[["Likes","Comments"]].sum().reset_index()
        fig = px.treemap(cat_df, path=["Category"], values="Likes",
                         color="Comments", color_continuous_scale=red_palette,
                         title="Engagement Breakdown by Category (Size=Likes, Color=Comments)")
        st.plotly_chart(fig, use_container_width=True)

        # 4. Views vs Upload Frequency
        st.markdown("### ⚡ Upload Frequency vs Monthly Views")
        freq_df = df.groupby("Month").agg(Uploads=("Video ID","count"), Views=("Views","sum")).reset_index()
        fig = px.bar(freq_df, x="Month", y="Views", color="Uploads", 
                     color_continuous_scale=red_palette,
                     title="Views vs Upload Frequency per Month")
        st.plotly_chart(fig, use_container_width=True)

        # 5. Engagement Rate Over Time
        st.markdown("### 🔥 Audience Engagement Trend")
        eng_df = df.groupby("Month")[["LikePerView","CommentPerView"]].mean().reset_index()
        fig = px.line(eng_df, x="Month", y=["LikePerView","CommentPerView"],
                      markers=True, color_discrete_sequence=red_palette,
                      title="Engagement Ratios over Time")
        st.plotly_chart(fig, use_container_width=True)

        # 6. Retention Proxy
        st.markdown("### ⏱ Retention Proxy (Likes per Minute of Video)")
        retention_df = df.groupby("Month")["LikePerMinute"].mean().reset_index()
        fig = px.bar(retention_df, x="Month", y="LikePerMinute", 
                     color="LikePerMinute", color_continuous_scale=red_palette,
                     title="Retention Proxy Trend (Likes / Minute)")
        st.plotly_chart(fig, use_container_width=True)

        # 7. Playlist Contribution
        st.markdown("### 📂 Playlist Contribution Share")
        pl_df = pd.DataFrame([{
            "Title": p["snippet"]["title"],
            "VideoCount": p["contentDetails"].get("itemCount", 0)
        } for p in playlists])
        if not pl_df.empty:
            fig = px.pie(pl_df, names="Title", values="VideoCount", 
                         color_discrete_sequence=red_palette,
                         title="Playlist Contribution Share (by Video Count)")
            st.plotly_chart(fig, use_container_width=True)

        # 8. Best Day to Publish
        st.markdown("### 📅 Average Views by Day of Week")
        dow = df.groupby("DayOfWeek")["Views"].mean().reindex(
            ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        ).reset_index()
        fig = px.bar(dow, x="DayOfWeek", y="Views", color="Views", 
                     color_continuous_scale=red_palette,
                     title="Average Views by Day of Week")
        st.plotly_chart(fig, use_container_width=True)

        # 9. Heatmap of Views by Hour & Day
        st.markdown("### 🕒 Heatmap: Views by Hour & Day")
        pivot = df.pivot_table(index="DayOfWeek", columns="Hour", values="Views", aggfunc="mean").fillna(0)
        fig = px.imshow(pivot, color_continuous_scale=red_palette, 
                        title="Optimal Publishing Time (Avg Views)")
        st.plotly_chart(fig, use_container_width=True)
