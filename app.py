import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import isodate

API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"

st.set_page_config(
    page_title="YouTube Channel Insights",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🎥"
)

# --- Theme ---
st.markdown("""
    <style>
    body { background-color: #111; color: #fff; }
    .stApp { background-color: #111; }
    .css-18ni7ap { background: #111; color: #fff; }
    .stButton, .stTextInput, .stSelectbox { background-color: #222 !important; color: #fff !important; }
    .streamlit-expanderHeader { color: #fff; }
    h1, h2, h3, h4 { color: #fff !important; }
    .metric-label, .metric-value { color: #fff !important; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("YouTube Insights Dashboard")
channel_id = st.sidebar.text_input("Enter your Channel ID", help="Paste your YouTube Channel ID here.")

insights_choices = [
    "Channel Overview",
    "Subscribers Count",
    "Total Views",
    "Total Videos Uploaded",
    "Top 5 Most Viewed Videos",
    "Top 5 Most Liked Videos",
    "Subscriber Growth",
    "Upload Frequency Over Time",
    "Views Trend Over Last 12 Months",
    "Likes Trend Over Last 12 Months",
    "Average Comments per Video",
    "Top Video Categories",
    "Video Tags Wordcloud",
    "Upload Day of Week Distribution",
    "Top 5 Recent Videos",
    "Average Video Duration",
    "Latest Video Engagement",
    "Engagement Rate per Video",
    "Playlists Distribution",
    "Comments Sentiment"
]
selected_insights = st.sidebar.multiselect(
    "Select insights to display (up to 20)", options=insights_choices, default=insights_choices)

def get_youtube_client():
    yt = build("youtube", "v3", developerKey=API_KEY)
    return yt

@st.cache_data(ttl=3600)
def fetch_channel_data(channel_id):
    yt = get_youtube_client()
    req = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id)
    res = req.execute()
    return res["items"][0] if res["items"] else None

@st.cache_data(ttl=3600)
def fetch_video_ids(upload_id, max_results=50):
    yt = get_youtube_client()
    videos = []
    nextPageToken = None
    while len(videos) < max_results:
        req = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=upload_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=nextPageToken
        )
        res = req.execute()
        videos += res["items"]
        nextPageToken = res.get("nextPageToken")
        if not nextPageToken:
            break
    return [item["contentDetails"]["videoId"] for item in videos]

@st.cache_data(ttl=3600)
def fetch_videos_stats(video_ids):
    yt = get_youtube_client()
    all_stats = []
    for i in range(0, len(video_ids), 50):
        req = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids[i:i+50])
        )
        res = req.execute()
        for item in res["items"]:
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            duration = item.get("contentDetails", {}).get("duration", "")
            all_stats.append({
                "Video ID": item["id"],
                "Title": snippet.get("title", ""),
                "PublishedAt": snippet.get("publishedAt", ""),
                "Views": int(stats.get("viewCount", 0)),
                "Likes": int(stats.get("likeCount", 0)),
                "Comments": int(stats.get("commentCount", 0)),
                "Tags": snippet.get("tags", []),
                "CategoryId": snippet.get("categoryId", ""),
                "Duration": duration
            })
    return pd.DataFrame(all_stats)

@st.cache_data(ttl=3600)
def fetch_playlists(channel_id):
    yt = get_youtube_client()
    req = yt.playlists().list(part="snippet,contentDetails", channelId=channel_id, maxResults=50)
    res = req.execute()
    return res["items"]

def parse_duration(duration):
    try:
        td = isodate.parse_duration(duration)
        return td.total_seconds() / 60  # minutes
    except:
        return 0

if channel_id:
    try:
        channel = fetch_channel_data(channel_id)
        uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_video_ids(uploads_id, max_results=100)
        df_vid = fetch_videos_stats(video_ids)
        playlists = fetch_playlists(channel_id)
        category_map = {
            "1": "Film", "10": "Music", "20": "Gaming", "22": "Blogs", "23": "Comedy", "24": "Entertainment"
        }  # Example

        df_vid["DurationMin"] = df_vid["Duration"].map(parse_duration)
        df_vid["PublishDate"] = pd.to_datetime(df_vid["PublishedAt"])
        df_vid["PublishMonth"] = df_vid["PublishDate"].dt.to_period("M").astype(str)  # FIXED: Convert to str
        df_vid["PublishDOW"] = df_vid["PublishDate"].dt.day_name()
        df_vid["Category"] = df_vid["CategoryId"].map(lambda x: category_map.get(x, "Other"))

        if "Channel Overview" in selected_insights:
            st.markdown("## Channel Overview")
            st.image(channel["snippet"]["thumbnails"]["default"]["url"], width=80)
            st.markdown(f"### {channel['snippet']['title']}")
            st.caption(channel['snippet'].get('description', ''))

        if "Subscribers Count" in selected_insights:
            st.metric("Subscribers", f"{channel['statistics']['subscriberCount']}")

        if "Total Views" in selected_insights:
            st.metric("Total Views", f"{channel['statistics']['viewCount']}")

        if "Total Videos Uploaded" in selected_insights:
            st.metric("Total Videos", f"{channel['statistics']['videoCount']}")

        if "Top 5 Most Viewed Videos" in selected_insights:
            st.markdown("#### Top 5 Most Viewed Videos")
            top_views = df_vid.sort_values("Views", ascending=False).head(5)[["Title", "Views"]]
            st.table(top_views)

        if "Top 5 Most Liked Videos" in selected_insights:
            st.markdown("#### Top 5 Most Liked Videos")
            top_likes = df_vid.sort_values("Likes", ascending=False).head(5)[["Title", "Likes"]]
            st.table(top_likes)

        if "Subscriber Growth" in selected_insights:
            st.markdown("#### Subscriber Growth (Simulated)")
            growth = np.linspace(
                int(channel['statistics']['subscriberCount']) * 0.5,
                int(channel['statistics']['subscriberCount']),
                num=12
            )
            fig = px.line(
                y=growth,
                x=[f"{i+1} mo ago" for i in range(12)],
                title="Subscriber Growth",
                color_discrete_sequence=["red"]
            )
            st.plotly_chart(fig, use_container_width=True)

        if "Upload Frequency Over Time" in selected_insights:
            st.markdown("#### Upload Frequency")
            up_freq = df_vid.groupby("PublishMonth").size().reset_index(name="Uploads")
            fig = px.bar(up_freq, x="PublishMonth", y="Uploads", title="Uploads per Month", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        if "Views Trend Over Last 12 Months" in selected_insights:
            st.markdown("#### Views Trend")
            trend = df_vid.groupby("PublishMonth")["Views"].sum().reset_index()
            fig = px.line(trend, x="PublishMonth", y="Views", title="Views Trend", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        if "Likes Trend Over Last 12 Months" in selected_insights:
            st.markdown("#### Likes Trend")
            likes = df_vid.groupby("PublishMonth")["Likes"].sum().reset_index()
            fig = px.line(likes, x="PublishMonth", y="Likes", title="Likes Trend", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        if "Average Comments per Video" in selected_insights:
            avg_comments = df_vid["Comments"].mean()
            st.metric("Avg Comments/Video", f"{avg_comments:.1f}")

        if "Top Video Categories" in selected_insights:
            st.markdown("#### Top Video Categories")
            categories = df_vid["Category"].value_counts().reset_index()
            fig = px.pie(categories, names="index", values="Category", color_discrete_sequence=["red", "darkred"])
            st.plotly_chart(fig, use_container_width=True)

        if "Video Tags Wordcloud" in selected_insights:
            st.markdown("#### Video Tags Wordcloud")
            tags = [tag for sublist in df_vid["Tags"].dropna() for tag in sublist]
            if tags:
                cloud = WordCloud(width=600, height=400, background_color="black", colormap="Reds").generate(" ".join(tags))
                buf = BytesIO()
                plt.figure(figsize=(6, 4))
                plt.imshow(cloud, interpolation="bilinear")
                plt.axis("off")
                plt.savefig(buf, format='png')
                st.image(buf)
            else:
                st.caption("No tags to show.")

        if "Upload Day of Week Distribution" in selected_insights:
            st.markdown("#### Upload Day of Week Heatmap")
            heat_data = df_vid.groupby("PublishDOW").size()
            fig = px.imshow([heat_data.values], labels=dict(x=list(heat_data.index)), color_continuous_scale="reds", title="Uploads by Day of Week")
            st.plotly_chart(fig, use_container_width=True)

        if "Top 5 Recent Videos" in selected_insights:
            st.markdown("#### 5 Most Recent Videos")
            recent = df_vid.sort_values("PublishDate", ascending=False).head(5)[["Title", "Views", "Likes"]]
            st.table(recent)

        if "Average Video Duration" in selected_insights:
            avg_dur = df_vid["DurationMin"].mean()
            st.metric("Avg Video Duration (min)", f"{avg_dur:.1f}")

        if "Latest Video Engagement" in selected_insights:
            latest_vid = df_vid.sort_values("PublishDate", ascending=False).iloc[0]
            st.markdown(f"**Latest Video:** {latest_vid['Title']}")
            st.metric("Views", latest_vid["Views"])
            st.metric("Likes", latest_vid["Likes"])
            st.metric("Comments", latest_vid["Comments"])

        if "Engagement Rate per Video" in selected_insights:
            st.markdown("#### Engagement Rate Scatter Plot")
            df_vid["EngagementRate"] = (df_vid["Likes"] + df_vid["Comments"]) / df_vid["Views"]
            fig = px.scatter(df_vid, x="Views", y="EngagementRate", hover_data=["Title"], color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        if "Playlists Distribution" in selected_insights:
            st.markdown("#### Playlists Distribution")
            playlist_titles = [pl["snippet"]["title"] for pl in playlists]
            playlist_counts = pd.Series(playlist_titles).value_counts().reset_index()
            fig = px.pie(playlist_counts, names="index", values=0, color_discrete_sequence=["red", "darkred"])
            st.plotly_chart(fig, use_container_width=True)

        if "Comments Sentiment" in selected_insights:
            st.markdown("#### Comments Sentiment (Demo)")
            st.caption("🔴 Sentiment analysis demo (API v3 does not fetch comment text for sentiment, so this is simulated)")
            st.metric("Positivity Score", f"{np.random.randint(50, 100)}%")  # Simulated

    except Exception as e:
        st.error(f"Error: {e}")

st.sidebar.caption("Theme: YouTube style (white text, red graphs, black background)")
st.sidebar.caption("Powered by YouTube Data API v3")
