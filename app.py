import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import isodate

# ===================================
# CONFIG
# ===================================
API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"   # Replace with your API key

st.set_page_config(
    page_title="YouTube BI Dashboard",
    layout="wide",
    page_icon="🎥",
)

# ===================================
# THEME: Full Dark Mode
# ===================================
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #FFFFFF; }
    h1, h2, h3, h4, h5, h6, .stMarkdown, .css-1v0mbdj { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #111111 !important; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: white; }
    .css-1clj7nx, .stDataFrame td { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Red Palette
red_palette = ['#ff0000','#d70000','#c60000','#b70000','#9b0000']

# ===================================
# YOUTUBE API HELPERS
# ===================================
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

# ===================================
# APP INTERFACE
# ===================================
st.sidebar.title("⚡ YouTube Channel Analyzer")
channel_id = st.sidebar.text_input("Enter Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("❌ Channel not found. Check your ID/API quota.")
    else:
        st.title(f"📊 BI Dashboard for {channel['snippet']['title']}")
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df_vid = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        # ---------------------------------
        # DATA PREPROCESS
        # ---------------------------------
        df_vid["DurationMin"] = df_vid["Duration"].map(parse_duration)
        df_vid["PublishedDate"] = pd.to_datetime(df_vid["PublishedAt"], errors='coerce')
        df_vid["Month"] = df_vid["PublishedDate"].dt.strftime("%Y-%m")
        df_vid["DayOfWeek"] = df_vid["PublishedDate"].dt.day_name()
        df_vid["Hour"] = df_vid["PublishedDate"].dt.hour
        df_vid["Year"] = df_vid["PublishedDate"].dt.year
        df_vid["Category"] = df_vid["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        # Engagement Ratios
        df_vid["LikeRatio"] = (df_vid["Likes"] / df_vid["Views"].replace(0, np.nan)).fillna(0)
        df_vid["CommentRatio"] = (df_vid["Comments"] / df_vid["Views"].replace(0, np.nan)).fillna(0)
        df_vid["EngagementRate"] = df_vid["LikeRatio"] + df_vid["CommentRatio"]

        # ---------------------------------
        # HEADER METRICS
        # ---------------------------------
        metric_cols = st.columns(5)
        with metric_cols[0]:
            st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=100)
        with metric_cols[1]:
            st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with metric_cols[2]:
            st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with metric_cols[3]:
            st.metric("Videos", f"{int(channel['statistics']['videoCount']):,}")
        with metric_cols[4]:
            st.metric("Playlists", f"{len(playlists):,}")

        st.markdown("---")

        # ===================================
        # INSIGHTS TABS (like Tableau Sheets)
        # ===================================
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Performance Trends", 
            "🎯 Engagement Analytics", 
            "🕒 Scheduling Insights", 
            "📂 Playlists & Content"
        ])

        # -----------------------
        # TAB 1: Performance
        # -----------------------
        with tab1:
            st.subheader("Uploads Over Time")
            year_selected = st.selectbox("Filter Year", sorted(df_vid["Year"].unique()))
            df_year = df_vid[df_vid["Year"]==year_selected]
            fig = px.bar(df_year.groupby("Month")["Video ID"].count().reset_index(),
                         x="Month", y="Video ID", text_auto=True,
                         title=f"Uploads in {year_selected}",
                         color="Video ID", color_continuous_scale=red_palette)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Top 10 Videos by Views")
            top_videos = df_vid.sort_values("Views", ascending=False).head(10)
            fig = px.bar(top_videos, x="Views", y="Title", orientation="h",
                         color="Views", color_continuous_scale=red_palette,
                         title="Most Popular Videos (by Views)")
            st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # TAB 2: Engagement
        # -----------------------
        with tab2:
            st.subheader("Engagement Rates by Video")
            min_views = st.slider("Min Views Filter", 0, int(df_vid["Views"].max()), 1000)
            filtered_eng = df_vid[df_vid["Views"]>=min_views]
            fig = px.scatter(filtered_eng, x="Views", y="EngagementRate", size="Comments",
                             color="LikeRatio", color_continuous_scale=red_palette,
                             hover_name="Title", title="Engagement Rate vs Views")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Likes vs Duration")
            category_choice = st.selectbox("Filter Category", sorted(df_vid["Category"].unique()))
            df_cat = df_vid[df_vid["Category"]==category_choice]
            fig = px.scatter(df_cat, x="DurationMin", y="Likes",
                             size="Comments", color="Likes", 
                             color_continuous_scale=red_palette,
                             hover_name="Title", title=f"Likes vs Duration ({category_choice})")
            st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # TAB 3: Scheduling
        # -----------------------
        with tab3:
            st.subheader("Optimal Publishing Time (Views by Hour/Day)")
            pivot = df_vid.pivot_table(index="DayOfWeek", columns="Hour", values="Views", aggfunc="sum").fillna(0)
            fig = px.imshow(pivot, color_continuous_scale=red_palette, title="Heatmap of Views by Hour/Day")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Uploads Per Day Calendar")
            cal = df_vid.groupby(df_vid["PublishedDate"].dt.date).size().reset_index(name="Uploads")
            fig = px.scatter(cal, x="PublishedDate", y="Uploads",
                             color="Uploads", color_continuous_scale=red_palette,
                             title="Daily Upload Activity")
            st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # TAB 4: Playlists
        # -----------------------
        with tab4:
            st.subheader("Playlists Overview")
            pl_df = pd.DataFrame([{
                "Title": p["snippet"]["title"],
                "VideoCount": p["contentDetails"].get("itemCount", "N/A")
            } for p in playlists])
            st.dataframe(pl_df)

            st.subheader("Cumulative Views Growth Over Time")
            growth = df_vid.sort_values("PublishedDate")
            growth["CumulativeViews"] = growth["Views"].cumsum()
            fig = px.area(growth, x="PublishedDate", y="CumulativeViews",
                          color_discrete_sequence=[red_palette[0]],
                          title="Cumulative Views Growth")
            st.plotly_chart(fig, use_container_width=True)
