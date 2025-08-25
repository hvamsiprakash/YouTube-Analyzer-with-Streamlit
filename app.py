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

        if date_filter and not df_vid.empty:
            min_date, max_date = df_vid["PublishedDate"].min().date(), df_vid["PublishedDate"].max().date()
            start_date = sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
            end_date = sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)
            df_vid = df_vid[(df_vid["PublishedDate"].dt.date >= start_date) & (df_vid["PublishedDate"].dt.date <= end_date)]

        # Apply global filters
        df_vid = df_vid[df_vid["Category"].isin(category_filter)]
        df_vid = df_vid[df_vid["Views"] >= min_views]

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
            st.markdown("Uploads Per Month")
            up_month = df_vid["Month"].value_counts().sort_index()
            fig = px.bar(x=up_month.index, y=up_month.values, labels={'x':"Month",'y':'Uploads'}, color=up_month.values, color_continuous_scale='reds', title="Uploads per Month")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("Top Videos by Views")
            top_vids = df_vid.sort_values("Views", ascending=False).head(10)
            fig = px.bar(top_vids, x="Views", y="Title", orientation='h', color="Views", color_continuous_scale='reds', title="Top Videos by Views")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("Top Videos by Likes")
            top_likes = df_vid.sort_values("Likes", ascending=False).head(10)
            fig = px.bar(top_likes, x="Title", y="Likes", color="Likes", color_continuous_scale='reds', title="Top Videos by Likes")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("Views & Likes Over Time")
            grouped = df_vid.groupby("Month")[["Views", "Likes"]].sum().reset_index()
            fig = px.line(grouped, x="Month", y=["Views", "Likes"], markers=True, color_discrete_sequence=['firebrick', 'indianred'])
            st.plotly_chart(fig, use_container_width=True)

            # Advanced Replacement: Heatmap of Likes by Hour and Day
            st.markdown("Heatmap: Likes by Hour and Day")
            likes_heatmap_data = df_vid.groupby(["DayOfWeek", "Hour"])["Likes"].sum().unstack(fill_value=0)
            hour_col, chart_col = st.columns([1,5])
            with hour_col:
                selected_hour = st.selectbox("Filter Hour", sorted(df_vid["Hour"].unique()), key="likes_heat_hour")
            with chart_col:
                likes_filtered = likes_heatmap_data.loc[:, selected_hour:selected_hour]
                fig = px.imshow(likes_filtered, color_continuous_scale="reds", title=f"Likes Heatmap (Hour={selected_hour})")
                st.plotly_chart(fig, use_container_width=True)

            # Advanced Replacement: Category sunburst by comments
            st.markdown("Sunburst of Comments by Category/Video")
            filter_cat = st.selectbox("Filter category", sorted(df_vid["Category"].unique()), key="sunburst_cat")
            sunburst_df = df_vid[df_vid["Category"] == filter_cat][["Category", "Title", "Comments"]]
            fig = px.sunburst(sunburst_df, path=["Category", "Title"], values="Comments", color="Comments", color_continuous_scale="reds", title="Comments Sunburst")
            st.plotly_chart(fig, use_container_width=True)

            # Advanced Replacement: Histogram views by selected year
            st.markdown("Histogram of Views by Year")
            year_col, chart_col = st.columns([1,5])
            with year_col:
                select_year = st.selectbox("Choose year", sorted(df_vid["Year"].unique()), key="hist_year")
            views_year_df = df_vid[df_vid["Year"] == select_year]
            with chart_col:
                fig = px.histogram(views_year_df, x="Views", nbins=15, color_discrete_sequence=['red'], title=f"Views Distribution ({select_year})")
                st.plotly_chart(fig, use_container_width=True)

            # Advanced Replacement: Scatterplot Likes vs Duration for selected category
            st.markdown("Scatterplot Likes vs Duration (Category)")
            cat_col, chart_col = st.columns([1,5])
            with cat_col:
                selected_cat = st.selectbox("Scatter Category", sorted(df_vid["Category"].unique()), key="scatter_likes_cat")
            filtered_df = df_vid[df_vid["Category"] == selected_cat]
            with chart_col:
                fig = px.scatter(filtered_df, x="DurationMin", y="Likes", color="Likes", color_continuous_scale='reds', size="Comments", hover_name="Title", title=f"Likes vs Duration ({selected_cat})")
                st.plotly_chart(fig, use_container_width=True)

            # Advanced Replacement: Line chart for Likes Cumulative over Date, with filter for min likes
            st.markdown("Likes Cumulative Growth (Min Likes Filter)")
            likes_min_col, chart_col = st.columns([1,5])
            with likes_min_col:
                min_likes_for_line = st.slider("Minimum Likes", min_value=int(df_vid["Likes"].min()), max_value=int(df_vid["Likes"].max()), value=0, key="min_likes_cum")
            likes_cum_df = df_vid[df_vid["Likes"] >= min_likes_for_line].sort_values("PublishedDate")
            likes_cum_df["CumulativeLikes"] = likes_cum_df["Likes"].cumsum()
            with chart_col:
                fig = px.line(likes_cum_df, x="PublishedDate", y="CumulativeLikes", color_discrete_sequence=["red"], title="Cumulative Likes Growth")
                st.plotly_chart(fig, use_container_width=True)

            # Playlists Table
            st.markdown("Playlists")
            pl = pd.DataFrame([{
                "Title": p["snippet"]["title"],
                "VideoCount": p["contentDetails"].get("itemCount", "N/A")
            } for p in playlists])
            st.dataframe(pl)

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
            fig = px.area(growth_df, x="PublishedDate", y="CumulativeViews", color_discrete_sequence=["red"], title="Cumulative Views Growth Over Time")
            st.plotly_chart(fig, use_container_width=True)

            # Videos per Day (Calendar-style scatter)
            st.markdown("Videos per Day")
            calendar_df = df_vid.groupby(df_vid["PublishedDate"].dt.date).size().reset_index(name="Uploads")
            calendar_col, chart_col = st.columns([1,5])
            with calendar_col:
                min_uploads = st.slider("Min uploads/day", min_value=1, max_value=int(calendar_df["Uploads"].max()), value=1, key="min_uploads_cal")
            calendar_df = calendar_df[calendar_df["Uploads"] >= min_uploads]
            with chart_col:
                fig = px.scatter(calendar_df, x="PublishedDate", y="Uploads", color="Uploads", color_continuous_scale="reds", title="Uploads per Day")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No video data found for this channel.")

    sidebar.caption("YouTube style • Red charts • Advanced insights • Filters in sidebar")
else:
    st.info("Enter a valid YouTube Channel ID to see insights.")



