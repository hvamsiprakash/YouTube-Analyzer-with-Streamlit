import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
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
    /* Global background */
    .stApp {
        background-color: #000 !important;
        color: white !important;
    }
    /* Cards */
    .card {
        background-color: #111;
        padding: 1rem;
        margin: 0.5rem 0.5rem 1rem 0;
        border-radius: 8px;
    }
    h1, h2, h3, h4 {
        color: white !important;
    }
    .stMetricLabel, .stMetricValue, .stMarkdown, .stDataFrame, .stCaption {
        color: white !important;
    }
    .stPlotlyChart {
        background: #111;
        padding: 0.5rem;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------
# UTILITY FUNCTIONS
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
                "Tags": snippet.get("tags", []),
                "CategoryId": snippet.get("categoryId", ""),
                "Duration": content.get("duration", "")
            })
    return pd.DataFrame(all_video)

@st.cache_data(ttl=1800)
def fetch_playlists(channel_id):
    yt = get_youtube_client()
    playlists = []
    nextPageToken = None
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

custom_reds = ["#ff0000", "#d70000", "#c60000", "#b70000", "#9b0000"]

# -------------------------------
# APP UI
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
        df_vid["PublishedDate"] = pd.to_datetime(df_vid["PublishedAt"], errors='coerce')
        df_vid["Month"] = df_vid["PublishedDate"].dt.strftime("%Y-%m")
        df_vid["DayOfWeek"] = df_vid["PublishedDate"].dt.day_name()
        df_vid["Year"] = df_vid["PublishedDate"].dt.year
        df_vid["Day"] = df_vid["PublishedDate"].dt.day
        df_vid["Hour"] = df_vid["PublishedDate"].dt.hour
        df_vid["Category"] = df_vid["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        st.markdown(f"<div class='card'><h2>Channel Overview</h2></div>", unsafe_allow_html=True)
        cards = st.columns(5)
        with cards[0]:
            st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=100)
        with cards[1]:
            st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with cards[2]:
            st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with cards[3]:
            st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
        if playlists:
            with cards[4]:
                st.metric("Total Playlists", f"{len(playlists):,}")

        st.markdown(f"<div class='card'><b>Description:</b> {channel['snippet'].get('description','No description')}</div>", unsafe_allow_html=True)

        if not df_vid.empty:

            # -------------------
            # Row 1
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Uploads per Month</h3>", unsafe_allow_html=True)
                up_month = df_vid["Month"].value_counts().sort_index()
                fig = px.bar(x=up_month.index, y=up_month.values,
                             color=up_month.values, color_continuous_scale=custom_reds,
                             labels={'x': "Month", 'y': 'Uploads'})
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Top Videos by Views</h3>", unsafe_allow_html=True)
                n_top = st.slider("Select Top N", 5, 20, 10, key="top_views")
                top_vids = df_vid.sort_values("Views", ascending=False).head(n_top)
                fig = px.bar(top_vids, x="Views", y="Title", orientation='h',
                             color="Views", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # Row 2
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Top Videos by Likes</h3>", unsafe_allow_html=True)
                n_top = st.slider("Select Top N Likes", 5, 20, 10, key="top_likes")
                top_likes = df_vid.sort_values("Likes", ascending=False).head(n_top)
                fig = px.bar(top_likes, x="Title", y="Likes", color="Likes",
                             color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Views vs Likes Over Time (Bubble Chart)</h3>", unsafe_allow_html=True)
                grouped = df_vid.groupby("Month")[["Views", "Likes"]].sum().reset_index()
                fig = px.scatter(grouped, x="Month", y="Views", size="Likes",
                                 color="Likes", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # Row 3 (NEW VISUALS instead of repeated)
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Likes by Day of Week (Radar/Polar)</h3>", unsafe_allow_html=True)
                likes_week = df_vid.groupby("DayOfWeek")["Likes"].sum().reset_index()
                fig = px.line_polar(likes_week, r="Likes", theta="DayOfWeek", line_close=True,
                                    color_discrete_sequence=[custom_reds[0]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Views Distribution by Year (Boxplot)</h3>", unsafe_allow_html=True)
                select_year = st.selectbox("Choose year", sorted(df_vid["Year"].unique()), key="hist_year")
                views_year_df = df_vid[df_vid["Year"] == select_year]
                fig = px.box(views_year_df, y="Views", points="all", color_discrete_sequence=[custom_reds[1]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # Row 4
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Comments Sunburst</h3>", unsafe_allow_html=True)
                filter_cat = st.selectbox("Filter category", sorted(df_vid["Category"].unique()), key="sunburst_cat")
                sunburst_df = df_vid[df_vid["Category"] == filter_cat][["Category", "Title", "Comments"]]
                fig = px.sunburst(sunburst_df, path=["Category", "Title"], values="Comments",
                                  color="Comments", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Likes vs Duration (Treemap)</h3>", unsafe_allow_html=True)
                selected_cat = st.selectbox("Select Category", sorted(df_vid["Category"].unique()), key="scatter_likes_cat")
                filtered_df = df_vid[df_vid["Category"] == selected_cat]
                fig = px.treemap(filtered_df, path=["Category", "Title"], values="Likes",
                                 color="DurationMin", color_continuous_scale=custom_reds)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # Row 5
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Likes Cumulative Growth</h3>", unsafe_allow_html=True)
                min_likes_for_line = st.slider("Minimum Likes", min_value=int(df_vid["Likes"].min()), max_value=int(df_vid["Likes"].max()), value=0)
                likes_cum_df = df_vid[df_vid["Likes"] >= min_likes_for_line].sort_values("PublishedDate")
                likes_cum_df["CumulativeLikes"] = likes_cum_df["Likes"].cumsum()
                fig = px.area(likes_cum_df, x="PublishedDate", y="CumulativeLikes",
                              color_discrete_sequence=[custom_reds[2]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Cumulative Views Growth</h3>", unsafe_allow_html=True)
                growth_df = df_vid.sort_values("PublishedDate")
                growth_df["CumulativeViews"] = growth_df["Views"].cumsum()
                fig = px.line(growth_df, x="PublishedDate", y="CumulativeViews",
                              color_discrete_sequence=[custom_reds[3]])
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # -------------------
            # Row 6
            # -------------------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='card'><h3>Playlists Table</h3>", unsafe_allow_html=True)
                pl = pd.DataFrame([{
                    "Title": p["snippet"]["title"],
                    "VideoCount": p["contentDetails"].get("itemCount", "N/A")
                } for p in playlists])
                st.dataframe(pl)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='card'><h3>Most Engaged Videos</h3>", unsafe_allow_html=True)
                most_engaged = df_vid.assign(TotalEngagement=lambda x: x["Likes"] + x["Comments"])
                st.dataframe(most_engaged.sort_values("TotalEngagement", ascending=False)[
                    ["Title", "TotalEngagement", "Likes", "Comments", "Views", "PublishedDate"]
                ].head(10))
                st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("Enter a valid YouTube Channel ID to see analytics.")
