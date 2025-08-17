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
    page_title="YouTube Analytics Pro Dashboard",
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
sidebar.title("Channel Insights Dashboard")
channel_id = sidebar.text_input("YouTube Channel ID", help="Paste your Channel ID here")

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
def fetch_all_videos(uploads_playlist_id, max_results=200):
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
        video_ids = fetch_all_videos(uploads_pid, max_results=200)
        df_vid = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        # Preprocessing
        df_vid["DurationMin"] = df_vid["Duration"].map(parse_duration)
        df_vid["PublishedDate"] = pd.to_datetime(df_vid["PublishedAt"])
        df_vid["Month"] = df_vid["PublishedDate"].dt.strftime("%Y-%m")
        df_vid["DayOfWeek"] = df_vid["PublishedDate"].dt.day_name()
        df_vid["Year"] = df_vid["PublishedDate"].dt.year
        df_vid["Day"] = df_vid["PublishedDate"].dt.day
        category_map = {
            "1": "Film", "2": "Autos", "10": "Music", "17": "Sports", "20": "Gaming", "23": "Comedy",
            "24": "Entertainment", "25": "News", "26": "Howto", "27": "Education", "28": "Science"
        }
        df_vid["Category"] = df_vid["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        # --------------------- UNIQUE CARDS (Just Once) ---------------------
        st.markdown(f"# Insights for: **{channel['snippet']['title']}**")
        st.markdown("## Channel Overview")

        cards = st.columns(4)
        with cards[0]:
            st.image(channel["snippet"]["thumbnails"]["high"]["url"], width=80)
        with cards[1]:
            st.metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
        with cards:
            st.metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
        with cards:
            st.metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")

        # Channel Description
        st.markdown(f"**Channel Description:** {channel['snippet'].get('description','No description')}")

        if not df_vid.empty:

            # 1. **Views & Likes by Month (Treemap + Filter)**
            st.markdown("## 1. Views & Likes by Month [Treemap]")
            months = list(df_vid["Month"].unique())
            month_select = st.selectbox("Filter: Month", options=months, index=len(months)-1, key="treemap_month")
            treemap_data = df_vid[df_vid["Month"] == month_select]
            fig = px.treemap(
                treemap_data,
                path=["Title"], values="Views",
                color="Likes",
                color_continuous_scale="reds",
                title=f"Views & Likes Distribution: {month_select}"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 2. **Category Distribution (Donut Pie with Filter)**
            st.markdown("## 2. Category Distribution [Donut Chart]")
            categories = sorted(df_vid["Category"].unique())
            cat_select = st.multiselect("Filter: Categories", categories, default=categories, key="cat_donut")
            cats_df = df_vid[df_vid["Category"].isin(cat_select)]
            category_summary = cats_df["Category"].value_counts().reset_index()
            fig = px.pie(
                category_summary, names="index", values="Category",
                hole=0.4, color_discrete_sequence=px.colors.sequential.Reds,
                title="Video Category Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 3. **Heatmap: Uploads by Day of Week and Hour**
            st.markdown("## 3. Uploads Timing Heatmap")
            df_vid["Hour"] = df_vid["PublishedDate"].dt.hour
            heatmap_data = df_vid.groupby(["DayOfWeek", "Hour"]).size().unstack(fill_value=0)
            fig = px.imshow(
                heatmap_data, color_continuous_scale="reds",
                title="Uploads Heatmap by Day & Hour"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 4. **Wordcloud of Video Tags**
            st.markdown("## 4. Video Tags Wordcloud")
            all_tags = [tag for tags in df_vid["Tags"].dropna() for tag in tags]
            tag_input = st.text_input("Enter keyword to highlight (optional):", "")
            if all_tags:
                wc = WordCloud(width=800, height=400, background_color="black",
                               colormap="Reds").generate(" ".join(all_tags))
                plt.figure(figsize=(8, 4))
                plt.imshow(wc, interpolation="bilinear")
                plt.axis("off")
                buf = BytesIO()
                plt.savefig(buf, format='png')
                plt.close()
                st.image(buf)
            else:
                st.info("No tags found.")

            # 5. **Bubble Chart: Likes vs Comments vs Duration (with Filter)**
            st.markdown("## 5. Likes vs Comments vs Duration [Bubble Chart]")
            y_metric = st.selectbox("Choose y-axis metric", ["Likes", "Comments"], key="bubble_y")
            fig = px.scatter(
                df_vid, x="DurationMin", y=y_metric, size="Views", color="Views",
                color_continuous_scale="reds", hover_name="Title",
                title=f"{y_metric} vs Duration (Bubble size = Views)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 6. **Line Chart: Views & Likes Over Time (Date Range Filter)**
            st.markdown("## 6. Views & Likes Over Time [Line Chart]")
            min_date, max_date = df_vid["PublishedDate"].min(), df_vid["PublishedDate"].max()
            date_range = st.slider("Filter: Date Range", min_value=min_date, max_value=max_date,
                                   value=(min_date, max_date), key="line_range")
            time_df = df_vid[(df_vid["PublishedDate"] >= date_range[0]) & (df_vid["PublishedDate"] <= date_range[1])]
            grouped_time = time_df.sort_values("PublishedDate").set_index("PublishedDate")
            fig = px.line(
                grouped_time, x=grouped_time.index, y=["Views", "Likes"],
                color_discrete_sequence=["darkred", "indianred"],
                title="Views & Likes Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 7. **Violin Chart: Views Distribution By Category**
            st.markdown("## 7. Views Distribution by Category [Violin Chart]")
            fig = px.violin(
                df_vid, y="Views", x="Category", color="Category",
                box=True, points="all", title="Views Spread by Video Category",
                color_discrete_sequence=px.colors.sequential.Reds
            )
            st.plotly_chart(fig, use_container_width=True)

            # 8. **Sunburst Chart: Category -> Video -> Likes**
            st.markdown("## 8. Likes Sunburst by Category & Video")
            sunburst_df = df_vid[["Category", "Title", "Likes"]]
            fig = px.sunburst(
                sunburst_df, path=["Category", "Title"], values="Likes",
                color="Likes", color_continuous_scale="reds",
                title="Likes by Category and Video"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 9. **Histogram: Video Duration Distribution (with bins slider)**
            st.markdown("## 9. Video Duration [Histogram]")
            bins = st.slider("Duration bins", 5, 30, 12, key="dur_bins")
            fig = px.histogram(
                df_vid, x="DurationMin", nbins=bins,
                color_discrete_sequence=["red"],
                title="Video Duration Distribution (min)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 10. **Top 10 Videos Table (with Sorting)**
            st.markdown("## 10. Top Videos Table")
            sort_by = st.selectbox("Sort by", ["Views", "Likes", "Comments"], key="top_sort")
            top_table = df_vid.sort_values(sort_by, ascending=False).head(10)
            st.dataframe(top_table[["Title", "Views", "Likes", "Comments", "DurationMin", "PublishedDate"]
                ].assign(PublishedDate=lambda x: x["PublishedDate"].dt.strftime("%Y-%m-%d %H:%M")))

            # --- End of Charts ---

        else:
            st.warning("No video data found for this channel.")

    sidebar.caption("YouTube style • All charts in reds • Advanced • Dynamic filtering under each chart")
else:
    st.info("Enter a valid YouTube Channel ID to see insights.")
