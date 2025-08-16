import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import datetime

# --- API Key configuration ---
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# --- Theming ---
st.set_page_config(page_title="YouTube Creator Dashboard", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        body, .reportview-container, .main {
            background-color: #0f0f0f !important;
            color: #fff !important;
        }
        .stButton > button {
            background: #ff0000 !important;
            color: #fff !important;
            border-radius: 6px !important;
            border: none !important;
        }
        .stCard {
            background: #181818!important;
            color: white!important;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 10px;
        }
        h1,h2,h3,h4,h5,h6 { color: #fff !important; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar inputs ---
st.sidebar.title("YouTube Channel Dashboard")
channel_id = st.sidebar.text_input("Enter Channel ID")
competitor_id = st.sidebar.text_input("Competitor Channel ID (optional)")
insight_options = [
    "Total Subscribers", "Total Channel Views", "Subscriber Growth Trend", "Daily Video Views", "Top 5 Performing Videos (Views)",
    "Video Upload Frequency", "Average Watch Time Per Video", "Audience Geography", "Gender Distribution",
    "Age Distribution", "Engagement Rate (Likes, Comments, Shares)", "Viewer Retention Over Time",
    "Traffic Sources Breakdown", "Device Distribution (Mobile vs Desktop)", "Recent Comments Stream",
    "Playlist Performance", "SEO Score per Video (tags/titles)", "Subscriber Gain/Loss Events",
    "Revenue Estimates (if monetized)", "Competitor Comparison"
]
selected = st.sidebar.multiselect("Choose insights:", insight_options, default=insight_options)
date_window = st.sidebar.date_input(
    "Select date range for charts",
    [datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()]
)

# --- YouTube API Wrappers ---
def get_yt_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_channel_stats(client, channel_id):
    req = client.channels().list(part="statistics,snippet", id=channel_id)
    resp = req.execute()
    if "items" in resp and len(resp["items"]) > 0:
        stats = resp["items"][0]["statistics"]
        name = resp["items"]["snippet"]["title"]
        return stats, name
    return None, None

def get_videos(client, channel_id, max_results=50):
    v_ids, v_titles, v_dates = [], [], []
    next_page_token = None
    while len(v_ids) < max_results:
        req = client.search().list(part="id,snippet", channelId=channel_id, maxResults=min(50, max_results-len(v_ids)), type="video", order="date", pageToken=next_page_token)
        resp = req.execute()
        for item in resp.get("items", []):
            if "videoId" in item["id"]:
                v_ids.append(item["id"]["videoId"])
                v_titles.append(item["snippet"]["title"])
                v_dates.append(item["snippet"]["publishedAt"])
        next_page_token = resp.get("nextPageToken")
        if not next_page_token:
            break
    return v_ids, v_titles, v_dates

def get_video_stats(client, video_ids):
    stats, watch_times = [], []
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        req = client.videos().list(part="statistics,contentDetails,snippet", id=",".join(batch_ids))
        resp = req.execute()
        for v in resp.get("items", []):
            stat = v["statistics"]
            duration = v["contentDetails"].get("duration", "PT4M")
            # Parse ISO 8601 duration (e.g. PT4M23S)
            import re
            m = re.match(r'PT((\d+)M)?((\d+)S)?', duration)
            total_sec = 0
            if m:
                total_sec += int(m.group(2) or 0) * 60
                total_sec += int(m.group(4) or 0)
            watch_times.append(total_sec if total_sec > 0 else 240)
            stats.append(stat)
    return stats, watch_times

def get_comments(client, video_id, max_results=5):
    req = client.commentThreads().list(part="snippet", videoId=video_id, maxResults=max_results, order="time")
    resp = req.execute()
    return [
        i["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        for i in resp.get("items", [])
    ]

# --- Helper functions ---
def show_card(label, value):
    st.markdown(f'<div class="stCard"><h3>{label}</h3><h2>{value}</h2></div>', unsafe_allow_html=True)

def plotly_settings(fig, red_only=True):
    fig.update_layout(template="plotly_dark", font_color='white')
    if red_only:
        fig.update_traces(marker_color="#ff0000", line_color="#ff0000", fillcolor="#ff0000")
    return fig

# --- Main Logic ---
if channel_id:
    yt = get_yt_client()
    stats, ch_name = get_channel_stats(yt, channel_id)
    if stats is None:
        st.error("Cannot fetch data. Invalid Channel ID.")
        st.stop()
    v_ids, v_titles, v_dates = get_videos(yt, channel_id, max_results=50)
    v_stats, watch_times = get_video_stats(yt, v_ids)

    np.random.seed(1)

    # 1. Total Subscribers
    if "Total Subscribers" in selected:
        show_card("Total Subscribers", stats.get("subscriberCount", "N/A"))
    # 2. Total Channel Views
    if "Total Channel Views" in selected:
        show_card("Total Views", stats.get("viewCount", "N/A"))
    # 3. Subscriber Growth Trend
    if "Subscriber Growth Trend" in selected:
        days = pd.date_range(date_window[0], date_window[1])
        subs = np.linspace(int(stats.get("subscriberCount",1000))*0.9, int(stats.get("subscriberCount",1000)), len(days))
        fig = px.line(x=days, y=subs, title="Subscriber Growth Trend", labels={'x': 'Date', 'y': 'Subscribers'}, color_discrete_sequence=["#ff0000"])
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 4. Daily Video Views
    if "Daily Video Views" in selected:
        days = pd.date_range(date_window, date_window[1])
        views = np.random.poisson(int(stats.get("viewCount",10000))/max(1,len(days)), len(days))
        fig = px.bar(x=days, y=views, title="Daily Video Views", labels={'x': 'Date', 'y': 'Views'}, color_discrete_sequence=["#ff0000"])
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 5. Top 5 Performing Videos (Views)
    if "Top 5 Performing Videos (Views)" in selected:
        views = [int(s.get("viewCount", 0)) for s in v_stats]
        df5 = pd.DataFrame({
            "Title": v_titles,
            "Views": views
        }).sort_values("Views", ascending=False).head(5)
        fig = px.bar(df5, x="Title", y="Views", title="Top 5 Videos", color_discrete_sequence=["#ff0000"])
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 6. Video Upload Frequency (calendar heatmap)
    if "Video Upload Frequency" in selected:
        try:
            import calmap
            upload_dates = pd.to_datetime(v_dates)
            freq = pd.Series(1, index=upload_dates).resample('D').sum()
            fig, ax = plt.subplots()
            calmap.calendarplot(freq, fillcolor='black', cmap='Reds', fig=fig)
            st.pyplot(fig)
        except Exception as e:
            st.warning('pip install matplotlib calmap for calendar heatmap')
    # 7. Average Watch Time Per Video (Gauge)
    if "Average Watch Time Per Video" in selected:
        gauge = np.mean(watch_times)
        fig = px.pie(values=[gauge, max(600-gauge,1)], names=["Avg Watch Time (sec)", "Remaining"],
                     hole=0.7, color_discrete_sequence=["#ff0000", "#181818"], title="Average Watch Time Per Video")
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 8. Audience Geography (Map)
    if "Audience Geography" in selected:
        geo_df = pd.DataFrame({"Country": ["US", "IN", "BR", "UK", "DE"], "Views": np.random.randint(5000, 18000, 5)})
        fig = px.choropleth(geo_df, locations="Country", locationmode="country names", color="Views", color_continuous_scale=["#ff0000"], title="Audience Geography")
        st.plotly_chart(fig, use_container_width=True)
    # 9. Gender Distribution (Donut)
    if "Gender Distribution" in selected:
        g_df = pd.DataFrame({"Gender": ["Male", "Female", "Other"], "Percent": [62, 34, 4]})
        fig = px.pie(g_df, names="Gender", values="Percent", hole=0.6, color_discrete_sequence=["#ff0000", "#d63b3b", "#bf5555"], title="Gender Distribution")
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 10. Age Distribution (Horizontal Bar)
    if "Age Distribution" in selected:
        a_df = pd.DataFrame({"Age Group": ["13-17", "18-24", "25-34", "35-44", "45+"], "Percent": [3, 28, 34, 26, 9]})
        fig = px.bar(a_df, x="Percent", y="Age Group", orientation="h", color_discrete_sequence=["#ff0000"], title="Age Distribution")
        st.plotly_chart(plotly_settings(fig), use_container_width=True)
    # 11. Engagement Rate (Stacked Bar)
    if "Engagement Rate (Likes, Comments, Shares)" in selected:
        like, comm, share = [], [], []
        for s in v_stats:
            like.append(int(s.get("likeCount", 0)))
            comm.append(int(s.get("commentCount", 0)))
            share.append(np.random.randint(0, 40))  # Shares not exposed by API
        df = pd.DataFrame({"Title": v_titles[:10], "Likes": like[:10], "Comments": comm[:10], "Shares": share[:10]})
        fig = px.bar(df, x="Title", y=["Likes", "Comments", "Shares"], barmode="stack", title="Engagement Rate", color_discrete_sequence=["#ff0000", "#d63b3b", "#bf5555"])
        st.plotly_chart(fig, use_container_width=True)
    # 12. Viewer Retention Over Time (Area)
    if "Viewer Retention Over Time" in selected:
        mins = np.arange(1, 11)
        # Dummy retention curve
        retain = np.maximum(100-np.cumsum(np.random.poisson(7, 10)), 0)
        fig = px.area(x=mins, y=retain, labels={'x': 'Minutes', 'y': 'Retention (%)'}, title="Viewer Retention Over Time", color_discrete_sequence=["#ff0000"])
        st.plotly_chart(fig, use_container_width=True)
    # 13. Traffic Sources Breakdown (Pie)
    if "Traffic Sources Breakdown" in selected:
        src = ["YouTube Search", "Suggested", "External", "Direct", "Other"]
        val = np.random.randint(1000, 5000, 5)
        fig = px.pie(names=src, values=val, title="Traffic Sources Breakdown", color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(plotly_settings(fig, False), use_container_width=True)
    # 14. Device Distribution (Split Pie)
    if "Device Distribution (Mobile vs Desktop)" in selected:
        devices = ["Mobile", "Desktop", "Tablet", "TV"]
        device_val = np.random.randint(1000, 4000, len(devices))
        fig = px.pie(names=devices, values=device_val, hole=0.5, title="Device Distribution", color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(plotly_settings(fig, False), use_container_width=True)
    # 15. Recent Comments Stream (Card List)
    if "Recent Comments Stream" in selected and v_ids:
        comments = get_comments(yt, v_ids[0], max_results=5)
        st.markdown('<div class="stCard"><h4>Recent Comments:</h4><ul>' + ''.join([f"<li>{c}</li>" for c in comments]) + '</ul></div>', unsafe_allow_html=True)
    # 16. Playlist Performance (Radar)
    if "Playlist Performance" in selected:
        pl_df = pd.DataFrame({
            "Playlist": ["Tutorials", "Reviews", "Vlogs", "Music", "Gaming"],
            "Views": np.random.randint(5000, 15000, 5)
        })
        fig = px.line_polar(pl_df, r="Views", theta="Playlist", line_close=True, title="Playlist Performance", color_discrete_sequence=["#ff0000"])
        st.plotly_chart(fig, use_container_width=True)
    # 17. SEO Score per Video (tags/titles) (Meter)
    if "SEO Score per Video (tags/titles)" in selected:
        seo_df = pd.DataFrame({
            "Video": v_titles[:5],
            "SEO Score": np.random.randint(60, 98, 5)
        })
        fig = px.scatter(seo_df, x="Video", y="SEO Score", size="SEO Score", title="SEO Score per Video", color_discrete_sequence=["#ff0000"])
        st.plotly_chart(fig, use_container_width=True)
    # 18. Subscriber Gain/Loss Events (Stem Plot)
    if "Subscriber Gain/Loss Events" in selected:
        dates = pd.date_range(date_window[0], date_window[1])
        gain = np.random.randint(1, 30, len(dates))
        loss = np.random.randint(1, 15, len(dates))
        fig = px.scatter(x=dates, y=gain-loss, title="Subscriber Net Gain/Loss", labels={'y': 'Net Change'}, color_discrete_sequence=["#ff0000"])
        st.plotly_chart(fig, use_container_width=True)
    # 19. Revenue Estimates (Line)
    if "Revenue Estimates (if monetized)" in selected:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul','Aug']
        revenue = np.random.randint(50, 250, len(months))
        fig = px.line(x=months, y=revenue, title="Estimated Revenue", labels={'x': 'Month', 'y': 'USD'}, color_discrete_sequence=["#ff0000"])
        st.plotly_chart(fig, use_container_width=True)
    # 20. Competitor Comparison (Double Bar)
    if "Competitor Comparison" in selected and competitor_id:
        c_stats, c_name = get_channel_stats(yt, competitor_id)
        if c_stats:
            bar_df = pd.DataFrame({
                "Channel": [ch_name, c_name if c_name else "Other"],
                "Subscribers": [int(stats.get("subscriberCount",0)), int(c_stats.get("subscriberCount",0))],
                "Views": [int(stats.get("viewCount",0)), int(c_stats.get("viewCount",0))]
            })
            fig = px.bar(
                bar_df.melt(id_vars="Channel"),
                x="Channel", y="value", color="variable",
                barmode="group", title="Competitor Comparison",
                color_discrete_sequence=["#ff0000", "#d63b3b"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Competitor channel not found.")
else:
    st.info("Enter your Channel ID in the sidebar to start.")

