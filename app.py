import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import isodate

# -------------------------------
# CONFIG & THEME
# -------------------------------
API_KEY = "AIzaSyDz8r5kvSnlkdQTyeEMS4hn0EMpXfUV1ig"

st.set_page_config(
    page_title="YouTube Advanced Analytics",
    layout="wide",
    page_icon=None,
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Background and base text */
    .stApp {
        background-color: #000 !important;
        color: #fff !important;
        padding: 0.5rem 1rem;
    }
    /* Card wrapper */
    .card {
        background-color: #222222;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0.75rem 1rem 0.75rem;
        box-shadow: 0 4px 10px rgba(215,0,0,0.4);
        min-height: 320px;
        color: white !important;
    }
    /* Heading style inside cards */
    .card h3 {
        margin-top: 0;
        margin-bottom: 0.8rem;
        color: #ff0000 !important;
        font-weight: 700;
        font-size: 1.3rem;
    }
    /* Filter label color */
    label[for] {
        color: white !important;
        font-size: 0.85rem;
        font-weight: 600;
    }
    /* Streamlit selectbox and slider adjustments inside cards */
    .stSelectbox > div > div > div, .stSlider > div > div {
        color: black !important;
        font-weight: 600;
    }
    /* Reduce spacing of metrics */
    .stMetric {
        padding-top: 0.2rem;
        padding-bottom: 0.2rem;
    }
    /* Plotly text inside charts */
    .main-svg text, .main-svg .legend text {
        fill: white !important;
    }
    /* Make charts backgrounds transparent dark */
    .js-plotly-plot {
        background-color: #222222 !important;
    }
    /* Align charts spacing */
    .block-container {
        max-width: 1280px;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }
    </style>
""", unsafe_allow_html=True)


# -------------------------------
# YOUTUBE API CLIENT & CACHE
# -------------------------------
def get_youtube_client():
    return build("youtube", "v3", developerKey=API_KEY)

@st.cache_data(ttl=1800)
def fetch_channel(channel_id):
    yt = get_youtube_client()
    res = yt.channels().list(part="snippet,statistics,contentDetails", id=channel_id).execute()
    return res["items"][0] if res.get("items") else None

@st.cache_data(ttl=1800)
def fetch_all_videos(uploads_playlist_id, max_results=300):
    yt = get_youtube_client()
    videos = []
    nextPageToken = None
    while len(videos) < max_results:
        result = yt.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=nextPageToken
        ).execute()
        videos.extend(result.get("items", []))
        nextPageToken = result.get("nextPageToken")
        if not nextPageToken:
            break
    return [item["contentDetails"]["videoId"] for item in videos]

@st.cache_data(ttl=1800)
def fetch_video_details(video_ids):
    yt = get_youtube_client()
    videos_data = []
    for i in range(0, len(video_ids), 50):
        res = yt.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids[i:i+50])
        ).execute()
        for item in res.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            videos_data.append({
                "id": item.get("id"),
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "duration": content.get("duration", "")
            })
    return pd.DataFrame(videos_data)

@st.cache_data(ttl=1800)
def fetch_playlists(channel_id):
    yt = get_youtube_client()
    playlists = []
    nextPageToken = None
    while True:
        res = yt.playlists().list(
            part="snippet,contentDetails",
            channelId=channel_id,
            maxResults=50,
            pageToken=nextPageToken
        ).execute()
        playlists.extend(res.get("items", []))
        nextPageToken = res.get("nextPageToken")
        if not nextPageToken:
            break
    return playlists

def parse_duration(duration_iso):
    try:
        td = isodate.parse_duration(duration_iso)
        return td.total_seconds() / 60  # minutes
    except:
        return 0

# -------------------------------
# MAIN
# -------------------------------
st.title("YouTube Advanced Analytics Dashboard")

channel_id = st.text_input("Enter YouTube Channel ID")

if channel_id:
    channel = fetch_channel(channel_id)
    if not channel:
        st.error("Channel not found or invalid Channel ID.")
    else:
        uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = fetch_all_videos(uploads_playlist_id)
        df = fetch_video_details(video_ids)
        playlists = fetch_playlists(channel_id)

        if df.empty:
            st.warning("No video data available for this channel.")
            st.stop()

        # Preprocessing
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
        df["duration_min"] = df["duration"].apply(parse_duration)
        df["year"] = df["published_at"].dt.year
        df["month"] = df["published_at"].dt.to_period('M').astype(str)
        df["day_of_week"] = df["published_at"].dt.day_name()
        df["engagement"] = (df["likes"] + df["comments"]) / df["views"].replace(0,1)
        df = df[df["views"] > 0]  # Ignore videos with zero views for engagement insights

        # Metrics at top in card style
        st.markdown(f"""
            <div class="card" style="display:flex; justify-content:space-around; flex-wrap: wrap; gap:1rem;">
                <div style="min-width:180px;">
                    <h3>Subscribers</h3>
                    <p style="font-size:1.5rem; color:#ff0000;">{int(channel['statistics']['subscriberCount']):,}</p>
                </div>
                <div style="min-width:180px;">
                    <h3>Total Views</h3>
                    <p style="font-size:1.5rem; color:#ff0000;">{int(channel['statistics']['viewCount']):,}</p>
                </div>
                <div style="min-width:180px;">
                    <h3>Total Videos</h3>
                    <p style="font-size:1.5rem; color:#ff0000;">{int(channel['statistics']['videoCount']):,}</p>
                </div>
                <div style="min-width:180px;">
                    <h3>Total Playlists</h3>
                    <p style="font-size:1.5rem; color:#ff0000;">{len(playlists):,}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Helper for rendering cards with dynamic width
        def render_card(title: str, filter_widget, plot_func):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
            filter_widget()
            plot_func()
            st.markdown('</div>', unsafe_allow_html=True)


        # 1. Upload Frequency Calendar-like Heatmap (Calendar heat with less clutter)
        def filter_upload_calendar():
            years = sorted(df["year"].dropna().unique())
            year_selected = st.selectbox("Select Year", years, key="upload_year_filter")
            st.session_state.upload_year = year_selected

        def plot_upload_calendar():
            year = st.session_state.get("upload_year", df["year"].min())
            df_year = df[df["year"] == year]
            # Group by date counting uploads
            uploads_per_date = df_year.groupby(df_year["published_at"].dt.date).size()
            if uploads_per_date.empty:
                st.info("No uploads in selected year.")
                return

            dates = pd.date_range(start=pd.Timestamp(f"{year}-01-01"), end=pd.Timestamp(f"{year}-12-31"))
            counts = [uploads_per_date.get(d.date(), 0) for d in dates]
            # Plot heatmap: Using scatter with colored square markers to emulate calendar heat
            fig = go.Figure(data=go.Heatmap(
                z=counts,
                x=dates.strftime("%b-%d"),
                y=["Uploads"],
                colorscale=[[0, '#9b0000'], [1, '#ff0000']],
                showscale=False
            ))

            fig.update_layout(
                height=120,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(tickangle=45, showgrid=False, zeroline=False),
                yaxis=dict(showticklabels=False)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 2. Views Growth Area Chart with filter on year range
        def filter_views_growth():
            years = sorted(df["year"].dropna().unique())
            yr_range = st.select_slider("Year Range", options=years, value=(years[0], years[-1]), key="view_growth_years")
            st.session_state.view_growth_years = yr_range

        def plot_views_growth():
            yr_min, yr_max = st.session_state.get("view_growth_years", (df["year"].min(), df["year"].max()))
            filt = (df["year"] >= yr_min) & (df["year"] <= yr_max)
            df_filt = df[filt].copy()
            df_filt["month"] = df_filt["published_at"].dt.to_period("M").astype(str)
            agg = df_filt.groupby("month")["views"].sum().reset_index()
            agg["cumulative_views"] = agg["views"].cumsum()
            fig = px.area(agg, x="month", y="cumulative_views",
                          labels={"month": "Month", "cumulative_views": "Cumulative Views"},
                          color_discrete_sequence=["#d70000"])
            fig.update_layout(margin=dict(t=30,l=20,r=20,b=20),
                              plot_bgcolor="#222", paper_bgcolor="#222",
                              font_color="white")
            st.plotly_chart(fig, use_container_width=True)

        # 3. Engagement Over Time Line Chart by Month (Likes+Comments / Views)
        def filter_engagement_over_time():
            nb_points = st.slider("Months to show", min_value=3, max_value=24, value=12, key="engage_month_count")

        def plot_engagement_over_time():
            nb_points = st.session_state.get("engage_month_count", 12)
            df["month"] = df["published_at"].dt.to_period("M").astype(str)
            df_group = df.groupby("month").agg({
                "likes": "sum",
                "comments": "sum",
                "views": "sum"
            }).tail(nb_points).reset_index()
            df_group["engagement_rate"] = (df_group["likes"] + df_group["comments"]) / df_group["views"].replace(0,1)

            fig = px.line(df_group, x="month", y="engagement_rate",
                          labels={"month":"Month", "engagement_rate":"Engagement Rate"},
                          color_discrete_sequence=["#c60000"])
            fig.update_layout(margin=dict(t=30,l=20,r=20,b=20),
                              plot_bgcolor="#222", paper_bgcolor="#222",
                              font_color="white",
                              yaxis_tickformat=".2%")
            st.plotly_chart(fig, use_container_width=True)

        # 4. Video Duration Distribution (Violin Plot)
        def filter_duration_dist():
            yr = st.selectbox("Year for Duration Dist.", sorted(df["year"].unique()), key="duration_year")

        def plot_duration_dist():
            yr = st.session_state.get("duration_year", df["year"].min())
            dfd = df[df["year"] == yr]
            if dfd.empty:
                st.info("No data available for the selected year.")
                return
            fig = px.violin(dfd, y="duration_min",
                            points="all",
                            labels={"duration_min": "Duration (min)"}, color_discrete_sequence=["#b70000"])
            fig.update_layout(margin=dict(t=30,l=20,r=20,b=20),
                              plot_bgcolor="#222", paper_bgcolor="#222",
                              font_color="white")
            st.plotly_chart(fig, use_container_width=True)

        # 5. Top Commented Videos (Sorted Table with paging)
        def filter_top_comments():
            n = st.slider("Number of Top Videos", min_value=5, max_value=30, value=10, key="top_comments_n")

        def plot_top_comments():
            n = st.session_state.get("top_comments_n", 10)
            top_comments = df.sort_values("comments", ascending=False).head(n)
            st.dataframe(top_comments[["title", "comments", "views", "likes", "duration_min", "published_at"]].rename(columns={
                "title":"Title", "comments":"Comments", "views":"Views", "likes":"Likes",
                "duration_min":"Duration (min)", "published_at":"Published At"
            }), height=320)

        # 6. Video Publishing Hour Preference Pie Chart
        def filter_publish_hour():
            days = sorted(df["day_of_week"].unique())
            day = st.selectbox("Select Day for Publishing Hour", days, key="publish_day_filter")

        def plot_publish_hour():
            day = st.session_state.get("publish_day_filter", df["day_of_week"].iloc[0])
            dfd = df[df["day_of_week"] == day]
            if dfd.empty:
                st.info("No videos published on this day.")
                return
            dfd["hour"] = dfd["published_at"].dt.hour
            counts = dfd["hour"].value_counts().sort_index()

            fig = px.pie(values=counts.values, names=counts.index,
                         color_discrete_sequence=custom_reds,
                         hole=0.4)
            fig.update_layout(title=f"Publishing Hours on {day}",
                              margin=dict(t=40,b=20,l=20,r=20),
                              font_color="white",
                              plot_bgcolor="#222", paper_bgcolor="#222")
            st.plotly_chart(fig, use_container_width=True)

        # 7. Likes vs. Views - Density Contour Plot (Advanced Insight)
        def filter_density_scatter():
            min_views = st.number_input("Min Views for Scatter", min_value=0, max_value=int(df["views"].max()), value=1000, step=500, key="min_views_scatter")

        def plot_density_scatter():
            thresh = st.session_state.get("min_views_scatter", 1000)
            dfd = df[df["views"] >= thresh]
            if dfd.empty:
                st.info("No videos found with selected minimum views.")
                return
            fig = px.density_contour(dfd, x="views", y="likes", nbinsx=30, nbinsy=30,
                                     color_discrete_sequence=["#ff0000"])
            fig.update_traces(contours_coloring="fill", contours_showlabels=True)
            fig.update_layout(
                xaxis_title="Views",
                yaxis_title="Likes",
                plot_bgcolor="#222", paper_bgcolor="#222",
                font_color="white",
                margin=dict(t=40,l=40,b=40,r=40))
            st.plotly_chart(fig, use_container_width=True)

        # 8. Daily Average Views Timeline (Line with Rolling Mean)
        def filter_avg_views():
            window = st.slider("Rolling window (days)", 1, 30, 7, key="rolling_window")

        def plot_avg_views():
            window = st.session_state.get("rolling_window", 7)
            daily_views = df.groupby(df["published_at"].dt.date)["views"].sum().reset_index()
            daily_views["rolling_avg_views"] = daily_views["views"].rolling(window).mean()
            fig = px.line(daily_views, x="published_at", y="rolling_avg_views",
                          labels={"published_at": "Date", "rolling_avg_views": f"{window}-Day Rolling Avg Views"},
                          color_discrete_sequence=["#d70000"])
            fig.update_layout(plot_bgcolor="#222", paper_bgcolor="#222", font_color="white",
                              margin=dict(t=30,l=30,r=30,b=30))
            st.plotly_chart(fig, use_container_width=True)


        # Layout: Render cards in rows with 2 or 3 cards as space allows, with spacing.
        # Use Streamlit container and columns dynamically for layout and spacing
        all_cards = [
            ("Uploads Per Year Calendar Heatmap", filter_upload_calendar, plot_upload_calendar),
            ("Views Growth Area Chart", filter_views_growth, plot_views_growth),
            ("Engagement Rate Over Time", filter_engagement_over_time, plot_engagement_over_time),
            ("Video Duration Distribution", filter_duration_dist, plot_duration_dist),
            ("Top Commented Videos", filter_top_comments, plot_top_comments),
            ("Publishing Hour by Day Pie Chart", filter_publish_hour, plot_publish_hour),
            ("Likes vs Views Density Contour", filter_density_scatter, plot_density_scatter),
            ("Daily Rolling Avg Views Timeline", filter_avg_views, plot_avg_views)
        ]

        # Responsively choose 2 or 3 per row depending on screen width (approximation)
        # Here, fixed 2 per row for neatness and card size minimization
        cols_per_row = 2
        for i in range(0, len(all_cards), cols_per_row):
            row_cards = all_cards[i:i+cols_per_row]
            cols = st.columns(cols_per_row, gap="large")
            for col, (title, filter_w, plot_f) in zip(cols, row_cards):
                with col:
                    render_card(title, filter_w, plot_f)

else:
    st.info("Enter a valid YouTube Channel ID to load analytics.")
