import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import isodate

# -------------------------------
# CONFIG
# -------------------------------
API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"


st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    layout="wide",
    page_icon=None,
    initial_sidebar_state="collapsed"
)

# -------------------------------
# CSS THEME
# -------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #000 !important;
        color: white !important;
    }
    .card {
        background-color: #111;
        padding: 1rem;
        margin: 0.5rem;
        border-radius: 10px;
    }
    h1, h2, h3, h4, h5 {
        color: white !important;
    }
    .stMetricLabel, .stMetricValue, .stMarkdown, .stDataFrame, .stCaption {
        color: white !important;
    }
    .stPlotlyChart {
        background: #111;
        border-radius: 10px;
        padding: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# UTILITIES
# -------------------------------
def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

@st.cache_data(ttl=1800)
def fetch_channel(channel_id):
    yt = get_youtube_client()
    req = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id)
    res = req.execute()
    if res["items"]:
        return res["items"][0]
    else:
        return None

@st.cache_data(ttl=1800)
def fetch_all_videos(uploads_playlist_id, max_results=300):
    yt = get_youtube_client()
    videos = []
    nextPageToken = None
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
                "Duration": content.get("duration", "")
            })
    return pd.DataFrame(all_video)

@st.cache_data(ttl=1800)
def fetch_playlists(channel_id):
    yt = get_youtube_client()
    playlists = []
    nextPageToken = None
    while True:
        req = yt.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=nextPageToken
        )
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

custom_reds = ["#ff0000", "#d70000", "#c60000", "#b70000", "#9b0000"]

# -------------------------------
# APP
# -------------------------------
st.title("YouTube Analytics Dashboard")

channel_id = st.text_input("Enter YouTube Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("Channel not found. Check Channel ID.")
    else:
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df_vid = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        # Preprocessing
        df_vid["DurationMin"] = df_vid["Duration"].map(parse_duration)
        df_vid["PublishedDate"] = pd.to_datetime(df_vid["PublishedAt"], errors="coerce")
        df_vid["Month"] = df_vid["PublishedDate"].dt.strftime("%Y-%m")
        df_vid["Year"] = df_vid["PublishedDate"].dt.year
        df_vid["DayOfWeek"] = df_vid["PublishedDate"].dt.day_name()

        # -------------------
        # GLOBAL DATE FILTER
        # -------------------
        if not df_vid.empty:
            min_date, max_date = df_vid["PublishedDate"].min().date(), df_vid["PublishedDate"].max().date()
            st.markdown("### Filter by Date Range")
            start_date, end_date = st.date_input("Select Range", [min_date, max_date])
            if isinstance(start_date, list):  # streamlit bug patch
                start_date, end_date = start_date[0], start_date[1]
            df_vid = df_vid[(df_vid["PublishedDate"].dt.date >= start_date) & (df_vid["PublishedDate"].dt.date <= end_date)]

        # -------------------
        # CHANNEL OVERVIEW
        # -------------------
        st.markdown("<div class='card'><h2>Channel Overview</h2></div>", unsafe_allow_html=True)
        cols = st.columns(5)
        with cols[0]:
            st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=100)
        with cols[1]:
            st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with cols[2]:
            st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with cols[3]:
            st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
        if playlists:
            with cols[4]:
                st.metric("Playlists", f"{len(playlists):,}")

        st.markdown(f"<div class='card'><b>Description:</b> {channel['snippet'].get('description','No description')}</div>", unsafe_allow_html=True)

        if not df_vid.empty:
            # -------------------
            # INSIGHTS (3 per row)
            # -------------------
            # Row 1
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Uploads by Month</h3>", unsafe_allow_html=True)
                up_month = df_vid["Month"].value_counts().sort_index()
                fig = px.bar(x=up_month.index, y=up_month.values,
                             color=up_month.values, color_continuous_scale=custom_reds,
                             labels={"x": "Month", "y": "Uploads"})
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><h3>Top Videos by Views</h3>", unsafe_allow_html=True)
                top_vids = df_vid.sort_values("Views", ascending=False).head(10)
                fig = px.bar(top_vids, x="Views", y="Title", orientation="h",
                             color="Views", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown("<div class='card'><h3>Top Videos by Likes</h3>", unsafe_allow_html=True)
                top_likes = df_vid.sort_values("Likes", ascending=False).head(10)
                fig = px.bar(top_likes, x="Likes", y="Title", orientation="h",
                             color="Likes", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Row 2 - Better Insights
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Views & Likes Over Time</h3>", unsafe_allow_html=True)
                grouped = df_vid.groupby("Month")[["Views", "Likes"]].sum().reset_index()
                fig = px.line(grouped, x="Month", y=["Views", "Likes"],
                              markers=True, color_discrete_sequence=custom_reds[:2])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><h3>Views by Day of Week</h3>", unsafe_allow_html=True)
                views_day = df_vid.groupby("DayOfWeek")["Views"].sum().reindex(
                    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
                fig = px.bar(x=views_day.index, y=views_day.values,
                             color=views_day.values, color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown("<div class='card'><h3>Engagement Rate (Likes+Comments per View)</h3>", unsafe_allow_html=True)
                df_vid["EngagementRate"] = (df_vid["Likes"] + df_vid["Comments"]) / df_vid["Views"].replace(0,1)
                fig = px.scatter(df_vid, x="Views", y="EngagementRate", size="Likes",
                                 hover_name="Title", color="EngagementRate", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Row 3
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Comments Over Time</h3>", unsafe_allow_html=True)
                comments_time = df_vid.groupby("Month")["Comments"].sum().reset_index()
                fig = px.area(comments_time, x="Month", y="Comments",
                              color_discrete_sequence=[custom_reds[0]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><h3>Cumulative Views Growth</h3>", unsafe_allow_html=True)
                growth_df = df_vid.sort_values("PublishedDate")
                growth_df["CumulativeViews"] = growth_df["Views"].cumsum()
                fig = px.area(growth_df, x="PublishedDate", y="CumulativeViews",
                              color_discrete_sequence=[custom_reds[2]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown("<div class='card'><h3>Cumulative Likes Growth</h3>", unsafe_allow_html=True)
                likes_df = df_vid.sort_values("PublishedDate")
                likes_df["CumulativeLikes"] = likes_df["Likes"].cumsum()
                fig = px.line(likes_df, x="PublishedDate", y="CumulativeLikes",
                              color_discrete_sequence=[custom_reds[3]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Row 4: Tables
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Playlists</h3>", unsafe_allow_html=True)
                pl = pd.DataFrame([{
                    "Title": p["snippet"]["title"],
                    "VideoCount": p["contentDetails"].get("itemCount", "N/A")
                } for p in playlists])
                st.dataframe(pl)
                st.markdown("</div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><h3>Most Engaged Videos</h3>", unsafe_allow_html=True)
                most_engaged = df_vid.assign(TotalEngagement=lambda x: x["Likes"] + x["Comments"])
                st.dataframe(most_engaged.sort_values("TotalEngagement", ascending=False)[
                    ["Title", "TotalEngagement", "Likes", "Comments", "Views", "PublishedDate"]
                ].head(10))
                st.markdown("</div>", unsafe_allow_html=True)

            with c3:
                st.markdown("<div class='card'><h3>Video Durations vs Views</h3>", unsafe_allow_html=True)
                fig = px.scatter(df_vid, x="DurationMin", y="Views", size="Likes",
                                 color="Views", color_continuous_scale=custom_reds, hover_name="Title")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Enter a valid YouTube Channel ID to see analytics.")
