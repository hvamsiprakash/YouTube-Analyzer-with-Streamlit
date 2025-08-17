import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import plotly.express as px
import plotly.graph_objects as go

# =================== CONFIG ===================
# Set your API key here
API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# =========== THEME SETUP ===========
st.set_page_config(layout="wide", page_title="YouTube Creator Dashboard")
custom_css = """
<style>
    .reportview-container {
        background: #181818;
        color: #FFF;
    }
    .markdown-text-container {
        color: #FFF;
    }
    .card-style {
        background-color: #222;
        color: #FFF;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 8px #900;
        margin-bottom: 20px;
        text-align: center;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# =================== API CLIENT ===================
def get_youtube_service():
    return build('youtube', 'v3', developerKey=API_KEY)

# =========== DATA FETCHING HELPERS ===========
def get_channel_details(channel_id):
    youtube = get_youtube_service()
    result = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()
    if not result["items"]:
        return None
    item = result["items"][0]
    return {
        "title": item["snippet"]["title"],
        "description": item["snippet"]["description"],
        "subs": int(item["statistics"]["subscriberCount"]),
        "views": int(item["statistics"]["viewCount"]),
        "videos": int(item["statistics"]["videoCount"]),
        "published": item["snippet"]["publishedAt"]
    }

def get_recent_videos(channel_id, max_results=50):
    youtube = get_youtube_service()
    # Get uploads playlist id
    playlists = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    uploads_id = playlists["items"]["contentDetails"]["relatedPlaylists"]["uploads"]
    # Get recent videos
    video_results = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_id,
        maxResults=max_results
    ).execute()
    video_ids = [item["contentDetails"]["videoId"] for item in video_results["items"]]
    # Get stats for each video
    videos_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()
    videos_data = []
    for item in videos_response["items"]:
        stats = item["statistics"]
        snippet = item["snippet"]
        videos_data.append({
            "id": item["id"],
            "title": snippet["title"],
            "publishedAt": snippet["publishedAt"],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "duration": item["contentDetails"]["duration"],
            "tags": ",".join(snippet.get("tags", []))
        })
    return videos_data

# Dummy helpers (replace with real drills if needed)
def get_subscriber_history(channel_id):
    # Simulated data. Replace with YouTube Analytics API response.
    dates = pd.date_range(end=pd.Timestamp.today(), periods=90)
    subs = pd.Series(1000 + (dates.dayofyear * 7 + dates.day * 3), index=dates)
    return pd.DataFrame({"date": dates, "subs": subs})

def get_video_views_history(video_data):
    # Simulated data, randomize based on publish dates
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    views = pd.Series((dates.dayofyear * 9 + dates.day * 5) % 4000, index=dates)
    return pd.DataFrame({"date": dates, "views": views})

def get_engagement_rate(video_data):
    rate = []
    for vid in video_data:
        total = vid["views"] if vid["views"] else 1
        rate.append((vid["likes"] + vid["comments"]) / total)
    return pd.Series(rate, index=[v["title"] for v in video_data])

def get_geo_stats(channel_id):
    # Simulated country data
    countries = ["US", "UK", "IN", "CA", "AU"]
    viewers = [3500, 980, 1200, 500, 620]
    return pd.DataFrame({"country": countries, "viewers": viewers})

# =================== DASHBOARD UI ===================
st.title("🎥 YouTube Creator Dashboard")

channel_id = st.text_input("Enter Channel ID:", value="", help="Paste your YouTube channel ID here.")

if channel_id:
    # ------ Fetch Data ------
    channel = get_channel_details(channel_id)
    if not channel:
        st.error("Channel not found. Check your Channel ID.")
    else:
        videos = get_recent_videos(channel_id)

        # ------ Sidebar: Choosing visible insights ------
        st.sidebar.header("Dashboard Customization")
        user_options = {
            "Subscriber Growth Trend": st.sidebar.checkbox("Show Subscriber Growth", value=True),
            "Daily Video Views": st.sidebar.checkbox("Show Daily Video Views", value=True),
            "Top Performing Videos": st.sidebar.checkbox("Show Top Videos", value=True),
            "Upload Frequency": st.sidebar.checkbox("Show Upload Frequency", value=True),
            "Geography": st.sidebar.checkbox("Show Audience Geography", value=True),
            "Demographics": st.sidebar.checkbox("Show Audience Demographics", value=True),
            "Engagement": st.sidebar.checkbox("Show Engagement Charts", value=True),
            "Retention": st.sidebar.checkbox("Show Viewer Retention", value=True),
            "Traffic Sources": st.sidebar.checkbox("Show Traffic Sources", value=True),
            "Device Distribution": st.sidebar.checkbox("Show Device Distribution", value=True),
            "Comments": st.sidebar.checkbox("Show Recent Comments", value=True),
            "Playlist Performance": st.sidebar.checkbox("Show Playlist Radar", value=True),
            "SEO Score": st.sidebar.checkbox("Show SEO Meter", value=True),
            "Subscriber Events": st.sidebar.checkbox("Show Subscriber Gain/Loss", value=True),
            "Revenue": st.sidebar.checkbox("Show Revenue Chart", value=True),
            "Competitor Comparison": st.sidebar.checkbox("Show Competitor Comparison", value=True),
        }

        # ============ Cards - Always Visible ============
        st.subheader("Channel Summary")
        cols = st.columns(4)
        cols[0].markdown(f"""
        <div class='card-style'>
            <h2>{channel['subs']:,}</h2>
            <span>Total Subscribers</span>
        </div>
        """, unsafe_allow_html=True)
        cols.markdown(f"""
        <div class='card-style'>
            <h2>{channel['views']:,}</h2>
            <span>Total Channel Views</span>
        </div>
        """, unsafe_allow_html=True)
        cols.markdown(f"""
        <div class='card-style'>
            <h2>{channel['videos']:,}</h2>
            <span>Videos Uploaded</span>
        </div>
        """, unsafe_allow_html=True)
        cols.markdown(f"""
        <div class='card-style'>
            <h2>{pd.to_datetime(channel['published']).date()}</h2>
            <span>Channel Launched</span>
        </div>
        """, unsafe_allow_html=True)

        # ============ Subscriber Growth ============
        if user_options["Subscriber Growth Trend"]:
            st.subheader("Subscriber Growth Trend")
            df_subs = get_subscriber_history(channel_id)
            period = st.selectbox("Growth Period", ["Week", "Month", "Year"])
            if period == "Week":
                df_subs_plot = df_subs.tail(7)
            elif period == "Month":
                df_subs_plot = df_subs.tail(30)
            else:
                df_subs_plot = df_subs
            fig = px.line(df_subs_plot, x="date", y="subs", template="plotly_dark", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Daily Video Views ============
        if user_options["Daily Video Views"]:
            st.subheader("Daily Video Views")
            date_range = st.date_input("Select Date Range", [])
            df_views = get_video_views_history(videos)
            fig = px.bar(df_views, x="date", y="views", template="plotly_dark", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Top Performing Videos ============
        if user_options["Top Performing Videos"]:
            st.subheader("Top 5 Performing Videos")
            sort_by = st.radio("Sort by", ["Views", "Engagement"])
            if sort_by == "Views":
                top_vids = sorted(videos, key=lambda v: v["views"], reverse=True)[:5]
            else:
                top_vids = sorted(videos, key=lambda v: (v["likes"] + v["comments"]), reverse=True)[:5]
            df_top = pd.DataFrame(top_vids)
            fig = px.bar(df_top, x="title", y="views", template="plotly_dark", color_discrete_sequence=["red"])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Upload Frequency (Calendar Heatmap) ============
        if user_options["Upload Frequency"]:
            st.subheader("Video Upload Frequency")
            months = [v["publishedAt"][:7] for v in videos]
            df_freq = pd.DataFrame(months, columns=["month"])
            freq_count = df_freq["month"].value_counts().reset_index()
            freq_count.columns = ["month", "uploads"]
            fig = px.density_heatmap(freq_count, x="month", y="uploads", template="plotly_dark", color_continuous_scale="reds")
            st.plotly_chart(fig, use_container_width=True)

        # ============ Average Watch Time Per Video ============
        st.subheader("Average Watch Time Per Video")
        # Dummy gauge, replace with real watch time
        avg_watch_time = 7.2  # minutes, sample value
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_watch_time,
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 15]}, 'bar': {'color': "red"}},
            title={'text': "Average Watch Time"}
        ))
        st.plotly_chart(fig, use_container_width=True)

        # ============ Audience Geography ============
        if user_options["Geography"]:
            st.subheader("Audience Geography")
            geo = get_geo_stats(channel_id)
            show_geo = st.checkbox("Show Countries", value=True)
            if show_geo:
                fig = px.choropleth(geo, locations="country", color="viewers",
                                   locationmode='country names',
                                   color_continuous_scale="reds", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        # ============ Gender + Age Distribution ============
        if user_options["Demographics"]:
            st.subheader("Audience Gender Distribution")
            # Dummy values
            gender_data = pd.DataFrame({
                "gender": ["Male", "Female"],
                "percentage": [62, 38]
            })
            show_type = st.radio("Show", ["Entire Audience", "Active Audience"])
            fig = px.pie(gender_data, names="gender", values="percentage",
                        color_discrete_sequence=["red", "#fff"], hole=0.5)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Audience Age Distribution")
            age_groups = ["13-17", "18-24", "25-34", "35-44", "45+"]
            age_perc = [6, 32, 41, 13, 8]  # Dummy
            age_data = pd.DataFrame({"age": age_groups, "percentage": age_perc})
            show_bracket = st.selectbox("Age Brackets", age_groups)
            fig = px.bar(age_data, x="percentage", y="age", orientation="h",
                         color="percentage", color_continuous_scale="reds", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # ============ Engagement Rate ============
        if user_options["Engagement"]:
            st.subheader("Engagement Rate (Likes, Comments, Shares)")
            df_engage = pd.DataFrame({
                "Video": [v["title"] for v in videos],
                "Likes": [v["likes"] for v in videos],
                "Comments": [v["comments"] for v in videos],
                "Shares": [v["comments"]//2 for v in videos]  # Shares dummy
            })
            sort_type = st.selectbox("Sort by (Engagement Type)", ["Likes", "Comments", "Shares"])
            df_engage = df_engage.sort_values(by=sort_type, ascending=False)
            fig = go.Figure(data=[
                go.Bar(name="Likes", x=df_engage["Video"], y=df_engage["Likes"], marker_color="red"),
                go.Bar(name="Comments", x=df_engage["Video"], y=df_engage["Comments"], marker_color="#fff"),
                go.Bar(name="Shares", x=df_engage["Video"], y=df_engage["Shares"], marker_color="#900")
            ])
            fig.update_layout(barmode='stack', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # ============ Viewer Retention ============
        if user_options["Retention"]:
            st.subheader("Viewer Retention Over Time")
            retention = pd.Series([80, 67, 58, 45, 31, 19], index=[0, 1, 2, 3, 4, 5])
            time_window = st.selectbox("Time Window", ["First 5 sec", "First 20 sec", "Entire video"])
            fig = px.area(x=retention.index, y=retention.values, color_discrete_sequence=["red"], template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        # ============ Traffic Sources Breakdown ============
        if user_options["Traffic Sources"]:
            st.subheader("Traffic Sources Breakdown")
            sources = ["Search", "Suggested", "External", "Other"]
            perc = [39, 31, 23, 7]  # Dummy
            focus_source = st.radio("Focus on", sources)
            fig = px.pie(names=sources, values=perc, color_discrete_sequence=["red", "#fff", "#900", "#333"])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Device Distribution ============
        if user_options["Device Distribution"]:
            st.subheader("Device Distribution")
            device = pd.DataFrame({
                "type": ["Mobile", "Desktop", "Tablet"],
                "perc": [68, 28, 4]
            })
            show_device = st.selectbox("Device Type", ["All", "Mobile", "Desktop", "Tablet"])
            df_device = device if show_device == "All" else device[device["type"] == show_device]
            fig = px.pie(df_device, names="type", values="perc", color_discrete_sequence=["red", "#fff", "#900"])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Recent Comments ============
        if user_options["Comments"]:
            st.subheader("Recent Comments Stream")
            # Dummy list; YouTube API v3 comments not available without Oauth (owner)
            comments = [
                {"user": "UserA", "comment": "Awesome video!", "date": "2025-07-12"},
                {"user": "UserB", "comment": "Loved the edit!", "date": "2025-07-09"},
                {"user": "UserC", "comment": "When is next?", "date": "2025-07-05"},
            ]
            for c in comments:
                st.markdown(f"""
                <div class='card-style'>
                    <b>{c['user']}</b> <span>{c['date']}</span><br>
                    {c['comment']}
                </div>
                """, unsafe_allow_html=True)

        # ============ Playlist Performance ============
        if user_options["Playlist Performance"]:
            st.subheader("Playlist Performance")
            # Simulate playlist radar chart (dummy)
            playlist_data = pd.DataFrame({
                "playlist": ["Tutorials", "Reviews", "Blogs", "Live", "Games"],
                "score": [75, 58, 62, 44, 95]
            })
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=playlist_data["score"], theta=playlist_data["playlist"],
                fill="toself", marker_color="red"
            ))
            fig.update_layout(polar=dict(bgcolor="#222"), template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # ============ SEO Score Meter ============
        if user_options["SEO Score"]:
            st.subheader("SEO Score per Video")
            scores = [80, 83, 91, 74, 68]
            recommendations = st.toggle("Show SEO Recommendations")
            fig = go.Figure(go.Indicator(
                mode= "gauge+number",
                value=scores[0],
                title={'text': "SEO Score (last video)"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "red"}}
            ))
            st.plotly_chart(fig, use_container_width=True)
            if recommendations:
                st.markdown("""SEO Tips:  
                • Use keyword-rich titles/tags  
                • Improve thumbnails  
                • Add closed captions  
                """)

        # ============ Subscriber Gain/Loss =============
        if user_options["Subscriber Events"]:
            st.subheader("Subscriber Gain/Loss Events")
            # Simulate stem plot with dummy data
            events = pd.Series([23, -14, 19, -7, 24], index=pd.date_range("2025-07-10", periods=5))
            datepick = st.date_input("Pick Date", [])
            fig = go.Figure(data=[go.Scatter(x=events.index, y=events.values, mode="markers+lines", marker_color="red")])
            st.plotly_chart(fig, use_container_width=True)

        # ============ Revenue Estimates ============
        if user_options["Revenue"]:
            st.subheader("Revenue Estimates")
            # Simulate line with dummy data
            month = pd.date_range("2025-03-01", periods=12, freq="M")
            revenue = pd.Series([91, 119, 138, 115, 98, 140, 163, 188, 140, 193, 150, 201], index=month)
            selector = st.selectbox("Select Period", ["Monthly", "Quarterly"])
            df_rev = revenue.resample("Q").mean() if selector == "Quarterly" else revenue
            fig = px.line(df_rev, x=df_rev.index, y=df_rev.values, color_discrete_sequence=["red"], template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # ============ Competitor Comparison ============
        if user_options["Competitor Comparison"]:
            st.subheader("Competitor Comparison")
            # Dummy competitor
            competitor_id = st.text_input("Enter Competitor Channel ID")
            if competitor_id:
                comp = get_channel_details(competitor_id)
                df_comp = pd.DataFrame({
                    "Metric": ["Subscribers", "Views"],
                    "You": [channel["subs"], channel["views"]],
                    "Competitor": [comp["subs"], comp["views"]]
                })
                fig = go.Figure(data=[
                    go.Bar(name="You", x=df_comp["Metric"], y=df_comp["You"], marker_color="red"),
                    go.Bar(name="Competitor", x=df_comp["Metric"], y=df_comp["Competitor"], marker_color="#fff")
                ])
                fig.update_layout(barmode='group', template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        # ============ Additional Charts ============
        st.subheader("Other Useful Insights")
        # Content Upload Times (when your audience is online)
        upload_times = ["Morning", "Afternoon", "Evening", "Night"]
        counts = [12, 28, 36, 7]
        fig = px.bar(x=upload_times, y=counts, color=counts, color_continuous_scale="reds", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        # Trending Hashtags in Titles
        hashtag_df = pd.DataFrame([
            {"tag": "#tutorial", "count": 7},
            {"tag": "#review", "count": 14},
            {"tag": "#live", "count": 4}
        ])
        fig = px.pie(hashtag_df, names="tag", values="count", color_discrete_sequence=["red", "#fff", "#900"])
        st.plotly_chart(fig, use_container_width=True)

