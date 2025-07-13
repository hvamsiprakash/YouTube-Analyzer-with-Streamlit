# Importing necessary libraries
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from dateutil.relativedelta import relativedelta

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Pro Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
def set_dark_theme():
    st.markdown("""
    <style>
    :root {
        --primary-color: #FF4B4B;
        --secondary-color: #0E1117;
        --text-color: #FFFFFF;
        --card-bg: #1A1D24;
    }
    .main {
        background-color: var(--secondary-color);
        color: var(--text-color);
    }
    .sidebar, .st-bw, .st-at, .st-cn {
        background-color: var(--secondary-color) !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color) !important;
    }
    .metric-box {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        color: #AAAAAA;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: var(--text-color);
        font-size: 28px;
        font-weight: 700;
        margin-top: 5px;
    }
    .metric-subtext {
        color: #AAAAAA;
        font-size: 12px;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

set_dark_theme()

# Cache YouTube data
@st.cache_data(ttl=3600, show_spinner="Fetching channel data...")
def get_channel_analytics(channel_id):
    try:
        channel_response = youtube.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails",
            id=channel_id
        ).execute()
        
        if not channel_response.get("items"):
            st.error("❌ Channel not found. Please check the Channel ID.")
            return None

        channel_info = channel_response["items"][0]

        # Fetch videos
        videos = []
        next_page_token = None
        for _ in range(10):  # Max 500 videos
            videos_response = youtube.search().list(
                channelId=channel_id,
                type="video",
                part="id,snippet",
                maxResults=50,
                order="date",
                pageToken=next_page_token
            ).execute()
            video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]

            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                video_response = youtube.videos().list(
                    part="statistics,snippet,contentDetails",
                    id=",".join(batch_ids)
                ).execute()
                for video in video_response.get("items", []):
                    stats = video["statistics"]
                    snippet = video["snippet"]
                    details = video["contentDetails"]
                    videos.append({
                        "title": snippet.get("title", "N/A"),
                        "video_id": video["id"],
                        "published_at": snippet.get("publishedAt", "N/A"),
                        "duration": details.get("duration", "PT0M"),
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "category_id": snippet.get("categoryId", "")
                    })

            next_page_token = videos_response.get("nextPageToken")
            if not next_page_token:
                break

        for video in videos:
            video["engagement"] = ((video["likes"] + video["comments"]) / max(1, video["views"])) * 100

        # Fetch playlists
        playlists = []
        next_page_token = None
        for _ in range(5):
            playlists_response = youtube.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            for playlist in playlists_response.get("items", []):
                playlists.append({
                    "title": playlist["snippet"]["title"],
                    "playlist_id": playlist["id"],
                    "item_count": playlist["contentDetails"]["itemCount"],
                    "thumbnail": playlist["snippet"]["thumbnails"]["high"]["url"]
                })
            next_page_token = playlists_response.get("nextPageToken")
            if not next_page_token:
                break

        channel_data = {
            "basic_info": {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "custom_url": channel_info["snippet"].get("customUrl", "N/A"),
                "published_at": channel_info["snippet"]["publishedAt"],
                "country": channel_info["snippet"].get("country", "N/A"),
                "thumbnail": channel_info["snippet"]["thumbnails"]["high"]["url"],
                "banner": channel_info["brandingSettings"].get("image", {}).get("bannerExternalUrl", "N/A"),
                "topics": channel_info.get("topicDetails", {}).get("topicCategories", [])
            },
            "statistics": {
                "view_count": int(channel_info["statistics"]["viewCount"]),
                "subscriber_count": int(channel_info["statistics"]["subscriberCount"]),
                "video_count": int(channel_info["statistics"]["videoCount"]),
                "hidden_subscriber_count": channel_info["statistics"]["hiddenSubscriberCount"]
            },
            "videos": sorted(videos, key=lambda x: x["views"], reverse=True),
            "playlists": playlists
        }

        return channel_data

    except Exception as e:
        st.error(f"❌ Error fetching channel data: {str(e)}")
        return None

# Estimate earnings based on simplified RPM assumptions
def calculate_earnings(videos_data, currency="USD", cpm_range="medium"):
    rpm_rates = {
        "USD": {
            "low": {"US": 1.0, "IN": 0.5, "other": 0.8},
            "medium": {"US": 3.0, "IN": 1.5, "other": 2.0},
            "high": {"US": 5.0, "IN": 2.5, "other": 3.5}
        },
        "INR": {
            "low": {"US": 80, "IN": 40, "other": 60},
            "medium": {"US": 240, "IN": 120, "other": 160},
            "high": {"US": 400, "IN": 200, "other": 280}
        },
        "EUR": {
            "low": {"US": 0.9, "IN": 0.45, "other": 0.7},
            "medium": {"US": 2.7, "IN": 1.35, "other": 1.8},
            "high": {"US": 4.5, "IN": 2.25, "other": 3.15}
        }
    }

    total_views = sum(video["views"] for video in videos_data)
    monthly_data = {}

    for video in videos_data:
        try:
            month = datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m")
            if month not in monthly_data:
                monthly_data[month] = {"views": 0, "videos": 0, "estimated_earnings": 0}
            monthly_data[month]["views"] += video["views"]
            monthly_data[month]["videos"] += 1
        except:
            continue

    for month in monthly_data:
        us_views = monthly_data[month]["views"] * 0.6
        in_views = monthly_data[month]["views"] * 0.1
        other_views = monthly_data[month]["views"] * 0.3
        us_earnings = (us_views / 1000) * rpm_rates[currency][cpm_range]["US"]
        in_earnings = (in_views / 1000) * rpm_rates[currency][cpm_range]["IN"]
        other_earnings = (other_views / 1000) * rpm_rates[currency][cpm_range]["other"]
        monthly_data[month]["estimated_earnings"] = us_earnings + in_earnings + other_earnings

    total_earnings = sum(month["estimated_earnings"] for month in monthly_data.values())

    return {
        "total_earnings": total_earnings,
        "monthly_earnings": monthly_data,
        "currency": currency,
        "cpm_range": cpm_range,
        "total_views": total_views,
        "estimated_rpm": total_earnings / (total_views / 1000) if total_views > 0 else 0
    }
# Helper functions
def parse_duration(duration):
    try:
        if duration.startswith('PT'):
            duration = duration[2:]
            hours = minutes = seconds = 0
            if 'H' in duration:
                hours, duration = duration.split('H')
                hours = int(hours)
            if 'M' in duration:
                minutes, duration = duration.split('M')
                minutes = int(minutes)
            if 'S' in duration:
                seconds = int(duration.replace('S', ''))
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except:
        return 0

def format_duration(seconds):
    h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
    return f"{h:02}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"

def format_number(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

# Main function
def youtube_dashboard():
    st.title("📊 YouTube Pro Analytics Dashboard")

    channel_id = st.text_input("🔍 Enter YouTube Channel ID", placeholder="e.g. UC_x5XG1OV2P6uZZ5FSM9Ttw")

    col1, col2, col3 = st.columns(3)
    currency = col1.selectbox("Currency", ["USD", "INR", "EUR"], index=0)
    cpm_range = col2.selectbox("CPM Level", ["low", "medium", "high"], index=1)
    time_range = col3.selectbox("Time Filter", ["All time", "Last 30 days", "Last 90 days", "Last 6 months", "Last year"])

    if st.button("🚀 Analyze Channel"):
        if not channel_id:
            st.warning("Please enter a valid Channel ID.")
            return

        channel_data = get_channel_analytics(channel_id)
        if not channel_data:
            return

        now = datetime.now()
        ranges = {
            "Last 30 days": now - timedelta(days=30),
            "Last 90 days": now - timedelta(days=90),
            "Last 6 months": now - relativedelta(months=6),
            "Last year": now - relativedelta(years=1),
            "All time": datetime.min
        }
        cutoff_date = ranges[time_range]

        # Filter videos
        videos = [v for v in channel_data["videos"] if datetime.strptime(v["published_at"], "%Y-%m-%dT%H:%M:%SZ") >= cutoff_date]
        earnings = calculate_earnings(videos, currency, cpm_range)

        df = pd.DataFrame(videos)
        df["published_at"] = pd.to_datetime(df["published_at"])
        df["duration_sec"] = df["duration"].apply(parse_duration)
        df["duration_fmt"] = df["duration_sec"].apply(format_duration)

        # -------------------- 📌 INSIGHT BLOCK --------------------

        st.markdown("## 📈 Channel Overview")
        ch = channel_data["basic_info"]
        st.image(ch["thumbnail"], width=150)
        st.markdown(f"""
        - **Name**: {ch['title']}
        - **Subscribers**: {format_number(channel_data['statistics']['subscriber_count'])}
        - **Total Views**: {format_number(channel_data['statistics']['view_count'])}
        - **Videos**: {channel_data['statistics']['video_count']}
        - **Country**: {ch['country']}
        - **Created On**: {datetime.strptime(ch['published_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")}
        """)

        # -------------------- 🔍 INSIGHTS (1–10) --------------------

        st.markdown("## 📊 Insights & Visualizations")

        colA, colB, colC = st.columns(3)
        colA.metric("Total Views", format_number(earnings['total_views']))
        colB.metric("Est. Revenue", f"{currency} {format_number(earnings['total_earnings'])}")
        colC.metric("Est. RPM", f"{earnings['estimated_rpm']:.2f} {currency}")

        # 1. Views over time
        st.subheader("1️⃣ Views Over Time")
        st.line_chart(df.set_index("published_at")["views"])

        # 2. Earnings over months
        st.subheader("2️⃣ Monthly Earnings")
        monthly_df = pd.DataFrame([
            {"Month": month, "Earnings": data["estimated_earnings"]}
            for month, data in earnings["monthly_earnings"].items()
        ])
        monthly_df["Month"] = pd.to_datetime(monthly_df["Month"])
        st.bar_chart(monthly_df.set_index("Month")["Earnings"])

        # 3. Top 10 Videos
        st.subheader("3️⃣ Top 10 Videos by Views")
        top_videos = df.sort_values("views", ascending=False).head(10)
        st.dataframe(top_videos[["title", "views", "likes", "comments", "engagement", "duration_fmt"]])

        # 4. Engagement Rate Distribution
        st.subheader("4️⃣ Engagement Rate vs Views")
        fig = px.scatter(
            df,
            x="views",
            y="engagement",
            hover_data=["title", "likes", "comments"],
            color="duration_sec",
            title="Engagement Rate Distribution",
            labels={"engagement": "Engagement (%)", "views": "Views"}
        )
        st.plotly_chart(fig)

        # 5. Duration Performance
        st.subheader("5️⃣ Video Duration vs Performance")
        fig2 = px.histogram(
            df,
            x="duration_sec",
            y="views",
            nbins=20,
            title="Duration vs Views"
        )
        st.plotly_chart(fig2)

        # 6. Posting Trends by Day
        st.subheader("6️⃣ Best Day to Post")
        df["weekday"] = df["published_at"].dt.day_name()
        weekday_views = df.groupby("weekday")["views"].mean().reindex([
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ])
        st.bar_chart(weekday_views)

        # 7. Likes to Views Ratio
        st.subheader("7️⃣ Likes-to-Views Ratio")
        df["likes_per_view"] = df["likes"] / df["views"]
        st.line_chart(df.set_index("published_at")["likes_per_view"])

        # 8. Comments Trend
        st.subheader("8️⃣ Comments Over Time")
        st.line_chart(df.set_index("published_at")["comments"])

        # 9. Playlist Overview
        st.subheader("9️⃣ Playlist Performance (Top 5)")
        for pl in channel_data["playlists"][:5]:
            st.markdown(f"- **{pl['title']}** — {pl['item_count']} videos")

        # 10. Posting Frequency
        st.subheader("🔟 Posting Frequency Trend")
        post_freq = df["published_at"].dt.to_period("M").value_counts().sort_index()
        st.bar_chart(post_freq)

        # -------------------- ✅ ADVANCED INSIGHTS (11–15) --------------------

        st.markdown("## 🧠 Advanced Creator Insights")

        # 11. Videos with High Engagement but Low Views
        st.subheader("11️⃣ Hidden Gems (High Engagement, Low Views)")
        gems = df[df["engagement"] > 20].sort_values("views").head(5)
        st.dataframe(gems[["title", "views", "engagement", "likes", "comments"]])

        # 12. Videos with Low Engagement but High Views
        st.subheader("1️⃣2️⃣ Underperforming (High Views, Low Engagement)")
        underperforming = df[df["engagement"] < 5].sort_values("views", ascending=False).head(5)
        st.dataframe(underperforming[["title", "views", "engagement", "likes", "comments"]])

        # 13. Best Video Length (Grouped)
        st.subheader("1️⃣3️⃣ Ideal Video Length Group")
        df["length_group"] = pd.cut(df["duration_sec"] / 60, bins=[0, 5, 10, 20, 60, 120], labels=["<5m", "5–10m", "10–20m", "20–60m", "60m+"])
        st.bar_chart(df.groupby("length_group")["views"].mean())

        # 14. Monthly Upload Count
        st.subheader("1️⃣4️⃣ Upload Count Per Month")
        upload_months = df["published_at"].dt.to_period("M").value_counts().sort_index()
        st.line_chart(upload_months)

        # 15. Top Performing Topics (if available)
        st.subheader("1️⃣5️⃣ Top Content Topics")
        topics = channel_data["basic_info"].get("topics", [])
        if topics:
            st.markdown("**Topics**: " + ", ".join(t.split("/")[-1].replace("_", " ").title() for t in topics[:5]))
        else:
            st.info("Topic metadata not available.")

# Run the app
if __name__ == "__main__":
    youtube_dashboard()
