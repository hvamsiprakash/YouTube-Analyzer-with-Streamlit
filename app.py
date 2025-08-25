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
    page_title="YouTube Advanced Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# CSS THEME
# -------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #000000 !important;
        color: white !important;
    }
    .card {
        background-color: #1a1a1a;
        padding: 1rem;
        margin: 0.6rem;
        border-radius: 12px;
    }
    h1, h2, h3, h4, h5 {
        color: white !important;
    }
    .stMetricLabel, .stMetricValue, .stMarkdown, .stDataFrame, .stCaption {
        color: white !important;
    }
    .stPlotlyChart {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 0.5rem;
    }
    .plotly .xtick text, .plotly .ytick text {
        fill: white !important;
    }
    .plotly .axis-title {
        fill: white !important;
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
    return None

@st.cache_data(ttl=1800)
def fetch_all_videos(uploads_playlist_id, max_results=300):
    yt = get_youtube_client()
    videos = []
    nextToken = None
    while len(videos) < max_results:
        req = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=nextToken
        )
        res = req.execute()
        videos += res["items"]
        nextToken = res.get("nextPageToken")
        if not nextToken:
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

import isodate
def parse_duration(duration):
    try:
        td = isodate.parse_duration(duration)
        return td.total_seconds() / 60
    except:
        return 0

custom_reds = ["#ff0000", "#d70000", "#c60000", "#b70000", "#9b0000"]

# -------------------------------
# APP
# -------------------------------
st.title("YouTube Advanced Analytics")

channel_id = st.text_input("Enter YouTube Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("Channel not found.")
    else:
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df = fetch_video_details(video_ids)

        if not df.empty:
            # Preprocessing
            df["DurationMin"] = df["Duration"].map(parse_duration)
            df["PublishedDate"] = pd.to_datetime(df["PublishedAt"], errors="coerce")
            df["Month"] = df["PublishedDate"].dt.strftime("%Y-%m")
            df["Year"] = df["PublishedDate"].dt.year
            df["DayOfWeek"] = df["PublishedDate"].dt.day_name()
            df["Hour"] = df["PublishedDate"].dt.hour

            # Channel KPIs
            st.markdown("<div class='card'><h2>Channel Stats</h2></div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
            with col2: st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
            with col3: st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
            with col4: st.metric("Video Uploads Fetched", f"{len(df):,}")

            # -------------------
            # ROW 1
            # -------------------
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><h3>Uploads by Month</h3>", unsafe_allow_html=True)
                fig = px.bar(df.groupby("Month").size().reset_index(name="Uploads"),
                             x="Month", y="Uploads", color="Uploads",
                             color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><h3>Average Views by Day of Week</h3>", unsafe_allow_html=True)
                avg_views = df.groupby("DayOfWeek")["Views"].mean().reindex(
                    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
                fig = px.bar(x=avg_views.index, y=avg_views.values, color=avg_views.values,
                             color_continuous_scale=custom_reds, labels={"x":"Day","y":"Avg Views"})
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # ROW 2
            # -------------------
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Top N Videos by Views</h3>", unsafe_allow_html=True)
                top_n = st.slider("Select Top N", 5, 20, 10, key="topn_views")
                top_vids = df.sort_values("Views", ascending=False).head(top_n)
                fig = px.bar(top_vids, x="Views", y="Title", orientation="h", color="Views",
                             color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><h3>Top N Videos by Engagement (Likes+Comments)</h3>", unsafe_allow_html=True)
                top_eng = df.assign(Engagement=df["Likes"]+df["Comments"]).sort_values("Engagement", ascending=False).head(10)
                fig = px.bar(top_eng, x="Engagement", y="Title", orientation="h", color="Engagement",
                             color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='card'><h3>Average Video Duration Over Time</h3>", unsafe_allow_html=True)
                dur_time = df.groupby("Month")["DurationMin"].mean().reset_index()
                fig = px.line(dur_time, x="Month", y="DurationMin", markers=True, color_discrete_sequence=[custom_reds[2]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # ROW 3
            # -------------------
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><h3>Likes vs Views (Correlation)</h3>", unsafe_allow_html=True)
                fig = px.scatter(df, x="Views", y="Likes", trendline="ols", color="Likes",
                                 color_continuous_scale=custom_reds, hover_name="Title")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><h3>Comments Trend Over Time</h3>", unsafe_allow_html=True)
                com_time = df.groupby("Month")["Comments"].sum().reset_index()
                fig = px.area(com_time, x="Month", y="Comments", color_discrete_sequence=[custom_reds[1]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # ROW 4
            # -------------------
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("<div class='card'><h3>Cumulative Views Growth</h3>", unsafe_allow_html=True)
                growth_df = df.sort_values("PublishedDate").copy()
                growth_df["CumulativeViews"] = growth_df["Views"].cumsum()
                fig = px.area(growth_df, x="PublishedDate", y="CumulativeViews",
                              color_discrete_sequence=[custom_reds[3]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><h3>Publishing Hour Analysis</h3>", unsafe_allow_html=True)
                hour_views = df.groupby("Hour")["Views"].mean().reset_index()
                fig = px.bar(hour_views, x="Hour", y="Views", color="Views",
                             color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='card'><h3>Engagement Rate Distribution</h3>", unsafe_allow_html=True)
                df["EngagementRate"] = (df["Likes"]+df["Comments"])/(df["Views"].replace(0,1))
                fig = px.histogram(df, x="EngagementRate", nbins=20, color_discrete_sequence=[custom_reds[4]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # ROW 5
            # -------------------
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><h3>Most Engaged Videos Table</h3>", unsafe_allow_html=True)
                most_eng = df.assign(TotalEngagement=lambda x:x["Likes"]+x["Comments"])
                st.dataframe(most_eng.sort_values("TotalEngagement", ascending=False)[
                    ["Title","Likes","Comments","Views","TotalEngagement","PublishedDate"]
                ].head(10))
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><h3>Views vs Duration</h3>", unsafe_allow_html=True)
                fig = px.scatter(df, x="DurationMin", y="Views", color="Views",
                                 color_continuous_scale=custom_reds, hover_name="Title")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
