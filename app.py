import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import isodate

API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"

st.set_page_config(
    page_title="YouTube Channel Analytics",
    layout="wide",
    page_icon="🎥",
    initial_sidebar_state="auto"
)

# --- Custom Theme ---
st.markdown("""
    <style>
    .stApp { background-color: #111; }
    div[data-testid="stMetricValue"] { color: #fff; }
    h1, h2, h3, h4, h5, h6 { color: #fff; }
    .stTable, .css-18ni7ap, .css-1v0mbdj, .css-1cpxqw2 { color: #fff; }
    .stPlotlyChart { background-color: #222;}
    [data-testid="stSidebar"] { background-color: #1B1B1B; }
    </style>
""", unsafe_allow_html=True)

sidebar = st.sidebar
sidebar.title("Channel Insights Dashboard")
channel_id = sidebar.text_input("YouTube Channel ID", help="Paste your Channel ID here")

insights_choices = [
    "Channel Card",
    "Subscribers Count",
    "Total Views",
    "Total Videos",
    "Most Viewed Videos",
    "Most Liked Videos",
    "Upload Frequency (Monthly)",
    "Video Categories Distribution",
    "Video Tags Wordcloud",
    "Uploads by Day of Week",
    "Recent Videos Table",
    "Average Video Duration",
    "Video Engagement (Likes/Views)",
    "Top Playlists Table"
]
selected_insights = sidebar.multiselect("Select insights (customize your view)", options=insights_choices, default=insights_choices)

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
def fetch_all_videos(uploads_playlist_id, max_results=100):
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

# ---- Main App ----
if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("Channel not found. Check your Channel ID and quota.")
    else:
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=100)
        df_vid = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        # Preprocessing
        df_vid["DurationMin"] = df_vid["Duration"].map(parse_duration)
        df_vid["PublishedDate"] = pd.to_datetime(df_vid["PublishedAt"])
        df_vid["Month"] = df_vid["PublishedDate"].dt.strftime("%Y-%m")
        df_vid["DayOfWeek"] = df_vid["PublishedDate"].dt.day_name()
        category_map = {
            "1": "Film", "2": "Autos", "10": "Music", "17": "Sports", "20": "Gaming", "23": "Comedy",
            "24": "Entertainment", "25": "News", "26": "Howto", "27": "Education", "28": "Science"
        }
        df_vid["Category"] = df_vid["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        st.markdown(f"# Insights for: **{channel['snippet']['title']}**")
        overview_cols = st.columns(3)
        if "Channel Card" in selected_insights:
            with overview_cols[0]:
                st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=100)
            with overview_cols[1]:
                st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
                st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
            with overview_cols:  # Corrected here: use specific column, NOT list
                st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
            st.markdown(f"**Channel Description:** {channel['snippet'].get('description','No description')}")

        metric_cols = st.columns(3)
        if "Subscribers Count" in selected_insights:
            with metric_cols[0]:
                st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        if "Total Views" in selected_insights:
            with metric_cols[1]:
                st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        if "Total Videos" in selected_insights:
            with metric_cols:
                st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")

        if not df_vid.empty:
            if "Most Viewed Videos" in selected_insights:
                mv_col1, mv_col2 = st.columns([2,1])
                with mv_col1:
                    st.markdown("#### Top 7 Most Viewed Videos (Bar Chart)")
                    top_vid = df_vid.sort_values("Views", ascending=False).head(7)
                    fig = px.bar(
                        top_vid,
                        x="Title", y="Views",
                        color="Views",
                        color_continuous_scale="reds",
                        title="Top Most Viewed Videos"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                with mv_col2:
                    st.markdown("#### Table")
                    st.table(top_vid[["Title", "Views"]])

            if "Most Liked Videos" in selected_insights:
                st.markdown("#### Top 7 Most Liked Videos (Horizontal Bar)")
                top_like = df_vid.sort_values("Likes", ascending=False).head(7)
                fig = px.bar(
                    top_like,
                    y="Title", x="Likes",
                    orientation="h", color="Likes",
                    color_continuous_scale="reds",
                    title="Top Most Liked Videos"
                )
                st.plotly_chart(fig, use_container_width=True)

            if "Upload Frequency (Monthly)" in selected_insights:
                st.markdown("#### Upload Frequency by Month")
                up_freq = df_vid["Month"].value_counts().sort_index()
                fig = px.line(
                    x=up_freq.index, y=up_freq.values,
                    labels={'x':"Month",'y':'Videos Uploaded'},
                    markers=True, title="Uploads per Month",
                    color_discrete_sequence=["red"]
                )
                st.plotly_chart(fig, use_container_width=True)

            if "Video Categories Distribution" in selected_insights:
                st.markdown("#### Video Categories Distribution")
                cat_counts = df_vid["Category"].value_counts().reset_index()
                cat_counts.columns = ["Category", "Count"]
                fig = px.pie(
                    cat_counts, names="Category", values="Count",
                    color_discrete_sequence=["red","darkred"],
                    title="Video Categories Proportion"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.table(cat_counts)

            if "Video Tags Wordcloud" in selected_insights:
                st.markdown("#### Video Tags Wordcloud")
                tags_list = []
                for tags in df_vid["Tags"].dropna():
                    tags_list.extend(tags)
                if tags_list:
                    cloud = WordCloud(width=600, height=400, background_color="black", colormap="Reds").generate(" ".join(tags_list))
                    buf = BytesIO()
                    plt.figure(figsize=(6, 4))
                    plt.imshow(cloud, interpolation="bilinear")
                    plt.axis("off")
                    plt.tight_layout(pad=0)
                    plt.savefig(buf, format='png')
                    st.image(buf)
                else:
                    st.caption("No tags to show.")

            if "Uploads by Day of Week" in selected_insights:
                st.markdown("#### Uploads by Day of Week")
                dow_counts = df_vid["DayOfWeek"].value_counts().reindex(
                    ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
                ).fillna(0)
                fig = px.bar(
                    x=dow_counts.index, y=dow_counts.values,
                    labels={'x': "Day of Week", 'y': "Uploads"},
                    color=dow_counts.values, color_continuous_scale="reds",
                    title="Uploads Distribution by Day"
                )
                st.plotly_chart(fig, use_container_width=True)

            if "Recent Videos Table" in selected_insights:
                st.markdown("#### Recent Videos")
                recent_videos = df_vid.sort_values("PublishedDate", ascending=False).head(10)
                st.dataframe(recent_videos[["Title", "Views", "Likes", "Comments", "DurationMin", "PublishedDate"]].assign(
                    PublishedDate=lambda x: x["PublishedDate"].dt.strftime("%Y-%m-%d %H:%M")
                ))

            if "Average Video Duration" in selected_insights:
                avg_duration = df_vid["DurationMin"].mean()
                st.metric("Average Video Duration (min)", f"{avg_duration:.2f}")

            if "Video Engagement (Likes/Views)" in selected_insights:
                st.markdown("#### Video Engagement Rate (Likes/Views Scatterplot)")
                df_vid["EngagementRate"] = df_vid["Likes"] / df_vid["Views"].replace(0, np.nan)
                fig = px.scatter(
                    df_vid, x="Views", y="EngagementRate",
                    color="EngagementRate", size="Likes",
                    hover_data=["Title"],
                    color_continuous_scale="reds",
                    title="Engagement Rate per Video"
                )
                st.plotly_chart(fig, use_container_width=True)

            if "Top Playlists Table" in selected_insights:
                st.markdown("#### Channel Playlists")
                pl = pd.DataFrame([{
                    "Title": p["snippet"]["title"],
                    "VideoCount": p["contentDetails"].get("itemCount", "N/A")
                } for p in playlists])
                st.dataframe(pl)
        else:
            st.warning("No video data found for this channel.")

    sidebar.caption("Theme: YouTube style (white text, red graphs, black background)")
    sidebar.caption("Advanced, uses only YouTube Data API v3, no simulated data.")
else:
    st.info("Enter a valid YouTube Channel ID to see insights.")
