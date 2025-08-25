import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import isodate

# --------- API KEY ---------
API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"

# ---------- Streamlit Config ----------
st.set_page_config(page_title="YouTube Creator Insights", layout="wide", page_icon="🎥")

# ---------- Custom Theme ----------
st.markdown("""
    <style>
    body { background-color: #111 !important; color: #fff !important; }
    .stApp { background-color: #111 !important; }
    .card {
        background-color: #1b1b1b; 
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px;
        box-shadow: 0px 0px 10px #c60000;
    }
    h1, h2, h3, h4, h5, h6 { color: #ff0000 !important; }
    .metric-label, .metric-value { color: #fff !important; }
    </style>
""", unsafe_allow_html=True)

# ---------- YouTube Client ----------
def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

@st.cache_data(ttl=1800)
def fetch_channel(channel_id):
    yt = get_youtube_client()
    req = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id)
    res = req.execute()
    return res["items"][0] if res["items"] else None

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

def parse_duration(duration):
    try:
        td = isodate.parse_duration(duration)
        return td.total_seconds() / 60  # minutes
    except:
        return 0

# ----------------- MAIN -----------------
st.title("📊 YouTube Creator Advanced Insights")

channel_id = st.text_input("Enter YouTube Channel ID:", "")

if channel_id:
    channel = fetch_channel(channel_id)
    if channel:
        uploads_pid = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_pid, max_results=300)
        df = fetch_video_details(video_ids)

        if df.empty:
            st.warning("No video data found.")
        else:
            # Preprocess
            df["PublishedDate"] = pd.to_datetime(df["PublishedAt"], errors='coerce')
            df["DurationMin"] = df["Duration"].map(parse_duration)
            df["Month"] = df["PublishedDate"].dt.strftime("%Y-%m")
            df["DayOfWeek"] = df["PublishedDate"].dt.day_name()
            df["DaysSince"] = (pd.Timestamp.today() - df["PublishedDate"]).dt.days

            # ----------- Dashboard Cards ----------
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            cols = st.columns(4)
            cols[0].metric("Subscribers", f"{int(channel['statistics']['subscriberCount']):,}")
            cols[1].metric("Total Views", f"{int(channel['statistics']['viewCount']):,}")
            cols[2].metric("Total Videos", f"{int(channel['statistics']['videoCount']):,}")
            cols[3].metric("Uploads Analyzed", f"{len(df)}")
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 1: Upload Consistency ----------
            st.markdown("<div class='card'><h3>📅 Upload Consistency</h3>", unsafe_allow_html=True)
            uploads_per_week = df.groupby(df["PublishedDate"].dt.to_period("W")).size()
            fig = px.line(uploads_per_week, markers=True, color_discrete_sequence=["#ff0000"])
            fig.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 2: Engagement Funnel ----------
            st.markdown("<div class='card'><h3>🎯 Engagement Funnel</h3>", unsafe_allow_html=True)
            total_views, total_likes, total_comments = df["Views"].sum(), df["Likes"].sum(), df["Comments"].sum()
            funnel_fig = go.Figure(go.Funnel(
                y=["Views", "Likes", "Comments"],
                x=[total_views, total_likes, total_comments],
                textinfo="value+percent previous",
                marker={"color": ["#ff0000", "#c60000", "#9b0000"]}
            ))
            funnel_fig.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="white")
            st.plotly_chart(funnel_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 3: Engagement Ratio Treemap ----------
            st.markdown("<div class='card'><h3>🌳 Engagement-to-Views Treemap</h3>", unsafe_allow_html=True)
            df["EngagementRate"] = (df["Likes"] + df["Comments"]) / df["Views"].replace(0, 1)
            treemap = px.treemap(df, path=["Title"], values="Views", color="EngagementRate",
                                 color_continuous_scale=["#9b0000", "#ff0000"])
            treemap.update_layout(paper_bgcolor="#111", font_color="white")
            st.plotly_chart(treemap, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 4: Longevity of Videos ----------
            st.markdown("<div class='card'><h3>📈 Video Longevity (Views vs Age)</h3>", unsafe_allow_html=True)
            longevity = px.scatter(df, x="DaysSince", y="Views", size="Likes", color="Comments",
                                   hover_name="Title", color_continuous_scale="reds")
            longevity.update_layout(paper_bgcolor="#111", font_color="white")
            st.plotly_chart(longevity, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 5: Rolling Growth ----------
            st.markdown("<div class='card'><h3>📊 Rolling 30-day Growth</h3>", unsafe_allow_html=True)
            monthly = df.groupby("Month")[["Views", "Likes", "Comments"]].sum().rolling(3).mean()
            fig = px.line(monthly, markers=True, color_discrete_sequence=["#ff0000", "#d70000", "#9b0000"])
            fig.update_layout(paper_bgcolor="#111", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ---------- Insight 6: Playlist Impact ----------
            st.markdown("<div class='card'><h3>📂 Playlist Impact (Top Videos)</h3>", unsafe_allow_html=True)
            top_vids = df.sort_values("Views", ascending=False).head(10)
            playlist_fig = px.bar(top_vids, x="Views", y="Title", orientation="h",
                                  color="Views", color_continuous_scale="reds")
            playlist_fig.update_layout(paper_bgcolor="#111", font_color="white")
            st.plotly_chart(playlist_fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.error("❌ Channel not found. Check the Channel ID and try again.")
