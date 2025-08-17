import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import isodate

API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"

st.set_page_config(
    page_title="YouTube Advanced Dashboard",
    layout="wide",
    page_icon="🎥",
    initial_sidebar_state="auto"
)

# --- Custom Theme ---
st.markdown("""
    <style>
    .stApp { background-color: #111 !important; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] { color: #fff !important; }
    h1, h2, h3, h4, h5, h6, .css-1v0mbdj, .css-1cpxqw2, .css-18ni7ap { color: #fff !important; }
    .stTable, .stDataFrame, .stMarkdown, .stCaption { color: #fff !important; }
    .stPlotlyChart { background-color: #222 !important;}
    [data-testid="stSidebar"] { background-color: #1B1B1B !important; }
    .css-1dp5vir { background-color: #111 !important; }
    </style>
""", unsafe_allow_html=True)

sidebar = st.sidebar
sidebar.title("Channel Insights & Filters")
channel_id = sidebar.text_input("YouTube Channel ID", help="Paste your Channel ID here")
date_filter = sidebar.checkbox("Enable Date Range Filter")
category_filter = sidebar.multiselect(
    "Filter by category", 
    ["Film", "Autos", "Music", "Sports", "Gaming", "Comedy", "Entertainment", "News", "Howto", "Education", "Science", "Other"], 
    default=["Film", "Autos", "Music", "Sports", "Gaming", "Comedy", "Entertainment", "News", "Howto", "Education", "Science", "Other"]
)
min_views = sidebar.number_input("Minimum Views (global filter)", min_value=0, value=0, step=100)

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

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("Channel not found. Check your Channel ID and quota.")
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

        # Sidebar Filter Application
        if date_filter and not df_vid.empty:
            min_date, max_date = df_vid["PublishedDate"].min().date(), df_vid["PublishedDate"].max().date()
            start_date = sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
            end_date = sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)
            df_vid = df_vid[(df_vid["PublishedDate"].dt.date >= start_date) & (df_vid["PublishedDate"].dt.date <= end_date)]

        # Apply global filters
        df_vid = df_vid[df_vid["Category"].isin(category_filter)]
        df_vid = df_vid[df_vid["Views"] >= min_views]

        # Cards summary
        st.markdown(f"# Insights for: **{channel['snippet']['title']}**")
        st.markdown("## Channel Overview")
        cards = st.columns(5)
        with cards[0]:
            st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=80)
        with cards[1]:
            st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with cards[2]:
            st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with cards[3]:
            st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
        if playlists:
            with cards[4]:
                st.metric("Total Playlists", f"{len(playlists):,}")
        st.markdown(f"**Channel Description:** {channel['snippet'].get('description','No description')}")

        if not df_vid.empty:
            # Uploads per Month
            st.markdown("Uploads Per Month")
            up_month = df_vid["Month"].value_counts().sort_index()
            fig = px.bar(x=up_month.index, y=up_month.values, labels={'x':"Month",'y':'Uploads'},
                         color=up_month.values, color_continuous_scale='reds', title="Uploads per Month")
            st.plotly_chart(fig, use_container_width=True)

            # Top Videos by Views
            st.markdown("Top Videos by Views")
            top_vids = df_vid.sort_values("Views", ascending=False).head(10)
            fig = px.bar(top_vids, x="Views", y="Title", orientation='h', color="Views",
                         color_continuous_scale='reds', title="Top Videos by Views")
            st.plotly_chart(fig, use_container_width=True)

            # Top Videos by Likes
            st.markdown("Top Videos by Likes")
            top_likes = df_vid.sort_values("Likes", ascending=False).head(10)
            fig = px.bar(top_likes, x="Title", y="Likes", color="Likes", color_continuous_scale='reds', title="Top Videos by Likes")
            st.plotly_chart(fig, use_container_width=True)

            # Views & Likes over Time
            st.markdown("Views & Likes Over Time")
            grouped = df_vid.groupby("Month")[["Views", "Likes"]].sum().reset_index()
            fig = px.line(grouped, x="Month", y=["Views", "Likes"], markers=True, color_discrete_sequence=['firebrick', 'indianred'])
            st.plotly_chart(fig, use_container_width=True)

            # Engagement Rate
            st.markdown("Engagement Rate")
            df_vid["EngagementRate"] = (df_vid["Likes"] + df_vid["Comments"]) / df_vid["Views"].replace(0, np.nan)
            fig = px.scatter(df_vid, x="Views", y="EngagementRate", size="Likes", color="EngagementRate",
                             color_continuous_scale='reds', hover_name="Title", title="Engagement Rate per Video")
            st.plotly_chart(fig, use_container_width=True)

            # Category Distribution Pie - FIXED
            st.markdown("Category Distribution")
            cat_counts = df_vid["Category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig = px.pie(cat_counts, names="Category", values="Count", hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Reds)
            st.plotly_chart(fig, use_container_width=True)

            # Uploads Heatmap
            st.markdown("Uploads Heatmap by Hour and Weekday")
            heatmap_data = df_vid.groupby(["DayOfWeek", "Hour"]).size().unstack(fill_value=0)
            fig = px.imshow(heatmap_data, color_continuous_scale="reds", title="Uploads Heatmap")
            st.plotly_chart(fig, use_container_width=True)

            # Duration Histogram
            st.markdown("Video Duration Distribution")
            fig = px.histogram(df_vid, x="DurationMin", nbins=12, color_discrete_sequence=["red"], title="Duration Histogram")
            st.plotly_chart(fig, use_container_width=True)

            # Duration by Category (Box Plot)
            st.markdown("Duration by Category")
            fig = px.box(df_vid, x="Category", y="DurationMin", color="Category",
                        color_discrete_sequence=px.colors.sequential.Reds, title="Duration per Category")
            st.plotly_chart(fig, use_container_width=True)

            # Likes by Category (Violin)
            st.markdown("Likes by Category (Violin)")
            fig = px.violin(df_vid, x="Category", y="Likes", box=True, points="all",
                            color="Category", color_discrete_sequence=px.colors.sequential.Reds)
            st.plotly_chart(fig, use_container_width=True)

            # Playlists Table
            st.markdown("Playlists")
            pl = pd.DataFrame([{
                "Title": p["snippet"]["title"],
                "VideoCount": p["contentDetails"].get("itemCount", "N/A")
            } for p in playlists])
            st.dataframe(pl)

            # Sunburst of Likes by Category/Video
            st.markdown("Sunburst of Likes by Category/Video")
            sunburst_df = df_vid[["Category", "Title", "Likes"]]
            fig = px.sunburst(sunburst_df, path=["Category", "Title"], values="Likes",
                            color="Likes", color_continuous_scale="reds", title="Likes Sunburst")
            st.plotly_chart(fig, use_container_width=True)

            # Treemap of Views by Category/Video
            st.markdown("Treemap of Views by Category/Video")
            fig = px.treemap(df_vid, path=["Category", "Title"], values="Views",
                            color="Views", color_continuous_scale="reds", title="Treemap: Views")
            st.plotly_chart(fig, use_container_width=True)
            
            # Most Engaged Videos Table
            st.markdown("Most Engaged Videos")
            most_engaged = df_vid.assign(TotalEngagement=lambda x: x["Likes"] + x["Comments"])
            st.dataframe(most_engaged.sort_values("TotalEngagement", ascending=False)[
                ["Title", "TotalEngagement", "Likes", "Comments", "Views", "PublishedDate"]
            ].head(10))

            # Cumulative Views Growth
            st.markdown("Cumulative Views Growth Over Time")
            growth_df = df_vid.sort_values("PublishedDate")
            growth_df["CumulativeViews"] = growth_df["Views"].cumsum()
            fig = px.area(growth_df, x="PublishedDate", y="CumulativeViews",
                        color_discrete_sequence=["red"], title="Cumulative Views Growth Over Time")
            st.plotly_chart(fig, use_container_width=True)

            # Scatter: Likes vs Comments vs Duration
            st.markdown("Likes vs Comments vs Duration (Bubble Chart)")
            fig = px.scatter(df_vid, x="DurationMin", y="Likes", size="Comments", color="Views",
                color_continuous_scale="reds", hover_name="Title", title="Bubble Chart (Likes/Comments/Duration)")
            st.plotly_chart(fig, use_container_width=True)

            # Videos per Day (Calendar-style scatter)
            st.markdown("Videos per Day")
            calendar_df = df_vid.groupby(df_vid["PublishedDate"].dt.date).size().reset_index(name="Uploads")
            fig = px.scatter(calendar_df, x="PublishedDate", y="Uploads", color="Uploads",
                            color_continuous_scale="reds", title="Uploads per Day")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("No video data found for this channel.")

    sidebar.caption("YouTube style • Red charts • Advanced insights • Filters in sidebar")
else:
    st.info("Enter a valid YouTube Channel ID to see insights.")
