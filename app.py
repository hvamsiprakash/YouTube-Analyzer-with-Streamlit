import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from googleapiclient.discovery import build
import pytz

# Initialize the YouTube API
API_KEY = "AIzaSyDGV_rw-styH4jKBMRr4fcX2-78jc79D3Q"
youtube = build('youtube', 'v3', developerKey=API_KEY)

# Set page config
st.set_page_config(
    page_title="YouTube Creator Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for YouTube theme
st.markdown("""
<style>
    .stApp {
        background-color: #000000;
        color: white;
    }
    .css-1d391kg, .css-1v3fvcr {
        background-color: #212121 !important;
    }
    .st-b7, .st-b8, .st-b9, .st-ba, .st-bb, .st-bc, .st-bd, .st-be, .st-bf, .st-bg, .st-bh, .st-bi, .st-bj, .st-bk, .st-bl, .st-bm, .st-bn, .st-bo, .st-bp, .st-bq {
        color: white !important;
    }
    .css-1aumxhk {
        background-color: #212121;
        color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .css-1v0mbdj {
        border-radius: 10px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    .stSelectbox, .stDateInput, .stSlider {
        background-color: #212121;
        color: white;
    }
    .stTextInput>div>div>input {
        color: white;
        background-color: #212121;
    }
    .st-bw {
        background-color: #FF0000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to get channel statistics
def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    
    if not response['items']:
        return None
    
    channel_data = {
        'channel_name': response['items'][0]['snippet']['title'],
        'subscribers': int(response['items'][0]['statistics']['subscriberCount']),
        'views': int(response['items'][0]['statistics']['viewCount']),
        'total_videos': int(response['items'][0]['statistics']['videoCount']),
        'playlist_id': response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    }
    return channel_data

# Function to get video IDs from playlist
def get_video_ids(playlist_id):
    video_ids = []
    request = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()
    
    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])
    
    next_page_token = response.get('nextPageToken')
    while next_page_token is not None:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])
        
        next_page_token = response.get('nextPageToken')
    
    return video_ids

# Function to get video details
def get_video_details(video_ids):
    all_video_stats = []
    
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=','.join(video_ids[i:i+50])
        )
        response = request.execute()
        
        for video in response['items']:
            try:
                like_count = int(video['statistics'].get('likeCount', 0))
            except:
                like_count = 0
                
            try:
                comment_count = int(video['statistics'].get('commentCount', 0))
            except:
                comment_count = 0
                
            video_stats = {
                'video_id': video['id'],
                'title': video['snippet']['title'],
                'published_at': video['snippet']['publishedAt'],
                'views': int(video['statistics'].get('viewCount', 0)),
                'likes': like_count,
                'comments': comment_count,
                'duration': video['contentDetails']['duration'],
                'thumbnail': video['snippet']['thumbnails']['high']['url']
            }
            all_video_stats.append(video_stats)
    
    return all_video_stats

# Function to generate mock data (for demonstration)
def generate_mock_data(channel_name):
    # Generate dates for the last 365 days
    dates = pd.date_range(end=datetime.today(), periods=365).date
    
    # Subscriber growth (mock)
    subs_start = np.random.randint(1000, 10000)
    subs_growth = np.random.normal(50, 20, 365).cumsum() + subs_start
    subs_growth = np.maximum(subs_growth, subs_growth[0])
    
    # Video views (mock)
    video_views = np.random.poisson(1000, 365) + np.random.randint(0, 5000, 365)
    
    # Top videos (mock)
    top_videos = []
    for i in range(10):
        top_videos.append({
            'title': f"{channel_name} Video {i+1}",
            'views': np.random.randint(10000, 500000),
            'likes': np.random.randint(100, 50000),
            'comments': np.random.randint(10, 5000),
            'published_at': (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime('%Y-%m-%d')
        })
    
    # Audience geography (mock)
    countries = ['US', 'UK', 'India', 'Canada', 'Germany', 'Brazil', 'Japan', 'Australia', 'France', 'Mexico']
    country_dist = np.random.dirichlet(np.ones(10), size=1)[0]
    
    # Age distribution (mock)
    age_groups = ['13-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    age_dist = np.random.dirichlet(np.ones(7), size=1)[0]
    
    # Gender distribution (mock)
    gender_dist = {'Male': np.random.uniform(0.4, 0.8), 'Female': np.random.uniform(0.2, 0.6)}
    gender_dist['Female'] = min(gender_dist['Female'], 1 - gender_dist['Male'])
    gender_dist['Other'] = 1 - gender_dist['Male'] - gender_dist['Female']
    
    # Traffic sources (mock)
    traffic_sources = {
        'YouTube Search': np.random.uniform(0.2, 0.4),
        'Suggested Videos': np.random.uniform(0.3, 0.5),
        'External': np.random.uniform(0.1, 0.3),
        'Direct': np.random.uniform(0.05, 0.15)
    }
    
    # Device distribution (mock)
    device_dist = {
        'Mobile': np.random.uniform(0.5, 0.8),
        'Desktop': np.random.uniform(0.15, 0.35),
        'Tablet': np.random.uniform(0.05, 0.15),
        'TV': np.random.uniform(0.01, 0.1)
    }
    
    # Video upload frequency (mock)
    upload_dates = [datetime.now() - timedelta(days=np.random.randint(1, 365)) for _ in range(50)]
    
    # Viewer retention (mock)
    retention_x = np.linspace(0, 100, 20)
    retention_y = np.exp(-retention_x/30) + np.random.normal(0, 0.02, 20)
    retention_y = np.maximum(retention_y, 0)
    
    # Engagement rate (mock)
    engagement_data = {
        'Likes': np.random.uniform(0.02, 0.1),
        'Comments': np.random.uniform(0.005, 0.03),
        'Shares': np.random.uniform(0.001, 0.02)
    }
    
    # Playlist performance (mock)
    playlists = ['Tutorials', 'Vlogs', 'Reviews', 'Live Streams', 'Q&A']
    playlist_performance = {
        'Views': np.random.randint(1000, 50000, 5),
        'Watch Time': np.random.randint(5000, 100000, 5),
        'Engagement': np.random.uniform(0.02, 0.1, 5)
    }
    
    # SEO scores (mock)
    seo_scores = np.random.randint(40, 90, 10)
    
    # Subscriber events (mock)
    sub_events = {
        'dates': [datetime.now() - timedelta(days=x) for x in np.random.randint(1, 365, 20)],
        'changes': np.random.randint(-100, 200, 20)
    }
    
    # Revenue estimates (mock)
    revenue_dates = pd.date_range(end=datetime.today(), periods=30).date
    revenue = np.random.normal(1000, 200, 30).cumsum()
    
    # Competitor data (mock)
    competitors = ['Competitor 1', 'Competitor 2', 'Competitor 3']
    comp_subs = np.random.randint(5000, 50000, 3)
    comp_views = np.random.randint(100000, 5000000, 3)
    
    return {
        'dates': dates,
        'subscriber_growth': subs_growth,
        'daily_views': video_views,
        'top_videos': top_videos,
        'countries': countries,
        'country_dist': country_dist,
        'age_groups': age_groups,
        'age_dist': age_dist,
        'gender_dist': gender_dist,
        'traffic_sources': traffic_sources,
        'device_dist': device_dist,
        'upload_dates': upload_dates,
        'retention': (retention_x, retention_y),
        'engagement': engagement_data,
        'playlists': playlists,
        'playlist_performance': playlist_performance,
        'seo_scores': seo_scores,
        'sub_events': sub_events,
        'revenue_dates': revenue_dates,
        'revenue': revenue,
        'competitors': competitors,
        'comp_subs': comp_subs,
        'comp_views': comp_views
    }

# Main dashboard function
def youtube_dashboard():
    st.title("YouTube Creator Dashboard")
    st.markdown("---")
    
    # Input channel ID
    channel_id = st.text_input("Enter YouTube Channel ID:", "UC_x5XG1OV2P6uZZ5FSM9Ttw")  # Default: Google Developers
    
    if channel_id:
        # Get channel data
        channel_data = get_channel_stats(channel_id)
        
        if not channel_data:
            st.error("Invalid Channel ID or unable to fetch data. Please check the ID and try again.")
            return
        
        st.sidebar.title("Options")
        st.sidebar.markdown(f"**Channel:** {channel_data['channel_name']}")
        st.sidebar.markdown(f"**Subscribers:** {channel_data['subscribers']:,}")
        
        # Generate mock data (in a real app, you would use actual API data)
        mock_data = generate_mock_data(channel_data['channel_name'])
        
        # Insight 1 & 2: Total Subscribers and Views (Cards)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background-color: #212121; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>Total Subscribers</h3>
                <h1 style="color: #FF0000;">{:,}</h1>
            </div>
            """.format(channel_data['subscribers']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: #212121; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>Total Channel Views</h3>
                <h1 style="color: #FF0000;">{:,}</h1>
            </div>
            """.format(channel_data['views']), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Insight 3: Subscriber Growth Trend
        st.header("Subscriber Growth Trend")
        time_period = st.radio("Select Time Period:", ["Week", "Month", "Year"], index=2, horizontal=True)
        
        if time_period == "Week":
            days = 7
        elif time_period == "Month":
            days = 30
        else:
            days = 365
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=mock_data['dates'][-days:],
            y=mock_data['subscriber_growth'][-days:],
            line=dict(color='red', width=3),
            mode='lines+markers',
            name='Subscribers'
        ))
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            xaxis_title='Date',
            yaxis_title='Subscribers',
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 4: Daily Video Views
        st.header("Daily Video Views")
        date_range = st.slider(
            "Select Date Range:",
            min_value=mock_data['dates'][0],
            max_value=mock_data['dates'][-1],
            value=(mock_data['dates'][-30], mock_data['dates'][-1])
        )
        
        mask = (pd.to_datetime(mock_data['dates']) >= pd.to_datetime(date_range[0])) & \
               (pd.to_datetime(mock_data['dates']) <= pd.to_datetime(date_range[1]))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=np.array(mock_data['dates'])[mask],
            y=np.array(mock_data['daily_views'])[mask],
            marker_color='red',
            name='Views'
        ))
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            xaxis_title='Date',
            yaxis_title='Views',
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 5: Top 5 Performing Videos
        st.header("Top Performing Videos")
        sort_by = st.selectbox("Sort Videos By:", ["Views", "Likes", "Comments"], index=0)
        
        top_videos = sorted(mock_data['top_videos'], key=lambda x: x[sort_by.lower()], reverse=True)[:5]
        
        if sort_by == "Views":
            color_scale = px.colors.sequential.Reds
        elif sort_by == "Likes":
            color_scale = px.colors.sequential.Oranges
        else:
            color_scale = px.colors.sequential.Purples
        
        fig = px.bar(
            pd.DataFrame(top_videos),
            x='title',
            y=sort_by.lower(),
            color=sort_by.lower(),
            color_continuous_scale=color_scale,
            labels={'title': 'Video Title', sort_by.lower(): sort_by},
            title=f"Top 5 Videos by {sort_by}"
        )
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            xaxis_title='Video Title',
            yaxis_title=sort_by,
            hovermode="x unified",
            coloraxis_showscale=False
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 6: Video Upload Frequency
        st.header("Video Upload Frequency")
        month_year = st.selectbox(
            "Select Month/Year:",
            options=[f"{m}-2023" for m in range(1, 13)],
            index=11
        )
        
        month = int(month_year.split('-')[0])
        year = int(month_year.split('-')[1])
        
        # Create calendar data
        cal = calendar.monthcalendar(year, month)
        days_in_month = calendar.monthrange(year, month)[1]
        dates_in_month = [datetime(year, month, day) for day in range(1, days_in_month+1)]
        
        # Count uploads per day
        upload_counts = {day: 0 for day in range(1, days_in_month+1)}
        for upload in mock_data['upload_dates']:
            if upload.year == year and upload.month == month:
                upload_counts[upload.day] += 1
        
        # Prepare data for heatmap
        heatmap_data = []
        for week in cal:
            row = []
            for day in week:
                if day == 0:
                    row.append(0)
                else:
                    row.append(upload_counts[day])
            heatmap_data.append(row)
        
        # Create heatmap
        fig = go.Figure(go.Heatmap(
            z=heatmap_data,
            colorscale='Reds',
            showscale=False,
            text=[["" if day == 0 else str(day) for day in week] for week in cal],
            hovertext=[["" if day == 0 else f"Day {day}: {upload_counts[day]} uploads" for day in week] for week in cal],
            texttemplate="%{text}",
            textfont={"color": "white"}
        ))
        
        fig.update_layout(
            title=f"Upload Frequency - {calendar.month_name[month]} {year}",
            xaxis=dict(
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ),
            yaxis=dict(
                tickvals=[0, 1, 2, 3, 4, 5],
                ticktext=['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                autorange="reversed"
            ),
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 7: Average Watch Time
        st.header("Average Watch Time")
        compare_period = st.checkbox("Compare to Previous Period", value=True)
        
        current_watch_time = np.random.uniform(3, 10)
        previous_watch_time = current_watch_time * np.random.uniform(0.8, 1.2)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_watch_time,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Minutes", 'font': {'color': 'white', 'size': 24}},
            delta={'reference': previous_watch_time if compare_period else None, 'increasing': {'color': "red"}},
            gauge={
                'axis': {'range': [None, 15], 'tickcolor': 'white'},
                'bar': {'color': "red"},
                'bgcolor': '#212121',
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 5], 'color': '#330000'},
                    {'range': [5, 10], 'color': '#660000'},
                    {'range': [10, 15], 'color': '#990000'}
                ],
            }
        ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 8: Audience Geography
        st.header("Audience Geography")
        show_countries = st.slider("Number of Countries to Show:", 3, 10, 5)
        
        fig = px.choropleth(
            pd.DataFrame({
                'country': mock_data['countries'][:show_countries],
                'percentage': mock_data['country_dist'][:show_countries] * 100
            }),
            locations='country',
            locationmode='country names',
            color='percentage',
            color_continuous_scale='Reds',
            range_color=(0, 100),
            labels={'percentage': 'Viewership %'},
            title='Audience Distribution by Country'
        )
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            geo=dict(bgcolor='rgba(0,0,0,0)'),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 9: Gender Distribution
        st.header("Audience Gender Distribution")
        audience_type = st.radio("Audience Type:", ["All Audience", "Active Audience"], index=0, horizontal=True)
        
        if audience_type == "Active Audience":
            # Adjust distribution slightly for active audience
            gender_data = {
                'Gender': list(mock_data['gender_dist'].keys()),
                'Percentage': [x * np.random.uniform(0.9, 1.1) for x in mock_data['gender_dist'].values()]
            }
            total = sum(gender_data['Percentage'])
            gender_data['Percentage'] = [x/total*100 for x in gender_data['Percentage']]
        else:
            gender_data = {
                'Gender': list(mock_data['gender_dist'].keys()),
                'Percentage': [x * 100 for x in mock_data['gender_dist'].values()]
            }
        
        fig = px.pie(
            gender_data,
            names='Gender',
            values='Percentage',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Reds_r,
            title='Gender Distribution'
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 10: Age Distribution
        st.header("Audience Age Distribution")
        show_brackets = st.multiselect(
            "Select Age Brackets to Show:",
            options=mock_data['age_groups'],
            default=mock_data['age_groups']
        )
        
        age_data = {
            'Age Group': mock_data['age_groups'],
            'Percentage': mock_data['age_dist'] * 100
        }
        age_df = pd.DataFrame(age_data)
        age_df = age_df[age_df['Age Group'].isin(show_brackets)]
        
        fig = px.bar(
            age_df,
            x='Percentage',
            y='Age Group',
            orientation='h',
            color='Percentage',
            color_continuous_scale='Reds',
            title='Age Distribution',
            labels={'Percentage': 'Percentage (%)', 'Age Group': 'Age Group'}
        )
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            yaxis={'categoryorder': 'total ascending'},
            coloraxis_showscale=False,
            xaxis_range=[0, 40]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 11: Engagement Rate
        st.header("Engagement Rate")
        engagement_type = st.selectbox("Select Engagement Metric:", ["Likes", "Comments", "Shares"])
        
        fig = go.Figure()
        
        for eng_type, rate in mock_data['engagement'].items():
            fig.add_trace(go.Bar(
                x=[eng_type],
                y=[rate * 100],
                name=eng_type,
                marker_color='red' if eng_type == engagement_type else '#444444',
                width=0.5
            ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title='Engagement Rates',
            yaxis_title='Percentage (%)',
            showlegend=False,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 12: Viewer Retention
        st.header("Viewer Retention Over Time")
        time_window = st.select_slider(
            "Select Time Window:",
            options=['First 10%', 'First 25%', 'First 50%', 'First 75%', 'Full Video'],
            value='Full Video'
        )
        
        window_map = {
            'First 10%': 10,
            'First 25%': 25,
            'First 50%': 50,
            'First 75%': 75,
            'Full Video': 100
        }
        
        max_x = window_map[time_window]
        x_vals = mock_data['retention'][0][:int(max_x/5)]
        y_vals = mock_data['retention'][1][:int(max_x/5)] * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            fill='tozeroy',
            line=dict(color='red'),
            name='Retention'
        ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title='Viewer Retention Curve',
            xaxis_title='Video Progress (%)',
            yaxis_title='Viewers Remaining (%)',
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 13: Traffic Sources
        st.header("Traffic Sources Breakdown")
        focus_source = st.selectbox(
            "Focus on:",
            options=list(mock_data['traffic_sources'].keys()),
            index=0
        )
        
        traffic_data = {
            'Source': list(mock_data['traffic_sources'].keys()),
            'Percentage': [x * 100 for x in mock_data['traffic_sources'].values()]
        }
        
        fig = px.pie(
            traffic_data,
            names='Source',
            values='Percentage',
            color='Source',
            color_discrete_map={focus_source: 'red'},
            title='Traffic Sources'
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#000000', width=2))
        )
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 14: Device Distribution
        st.header("Device Distribution")
        device_filter = st.multiselect(
            "Filter Devices:",
            options=list(mock_data['device_dist'].keys()),
            default=list(mock_data['device_dist'].keys())
        )
        
        device_data = {
            'Device': list(mock_data['device_dist'].keys()),
            'Percentage': [x * 100 for x in mock_data['device_dist'].values()]
        }
        device_df = pd.DataFrame(device_data)
        device_df = device_df[device_df['Device'].isin(device_filter)]
        
        fig = px.pie(
            device_df,
            names='Device',
            values='Percentage',
            hole=0.3,
            color_discrete_sequence=px.colors.sequential.Reds,
            title='Device Usage'
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#000000', width=2))
        )
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 15: Recent Comments
        st.header("Recent Comments")
        comment_count = st.slider("Number of Comments to Show:", 1, 20, 5)
        
        # Generate mock comments
        comments = []
        for i in range(comment_count):
            comments.append({
                'video': f"Video {i+1}",
                'comment': f"This is a sample comment #{i+1} about your video content.",
                'time': f"{np.random.randint(1, 24)} hours ago",
                'sentiment': np.random.choice(['Positive', 'Neutral', 'Negative'])
            })
        
        for comment in comments:
            sentiment_color = {
                'Positive': '#00aa00',
                'Neutral': '#aaaaaa',
                'Negative': '#ff0000'
            }[comment['sentiment']]
            
            st.markdown(f"""
            <div style="background-color: #212121; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid {sentiment_color}">
                <div style="display: flex; justify-content: space-between;">
                    <strong>{comment['video']}</strong>
                    <small>{comment['time']}</small>
                </div>
                <p style="margin-top: 5px; margin-bottom: 0;">{comment['comment']}</p>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <small>Sentiment: <span style="color: {sentiment_color}">{comment['sentiment']}</span></small>
                    <button style="background-color: #ff0000; color: white; border: none; border-radius: 3px; padding: 2px 8px; font-size: 12px;">Respond</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Insight 16: Playlist Performance
        st.header("Playlist Performance")
        metric = st.selectbox("Select Performance Metric:", ["Views", "Watch Time", "Engagement"])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=mock_data['playlist_performance'][metric],
            theta=mock_data['playlists'],
            fill='toself',
            line=dict(color='red'),
            name=metric
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(mock_data['playlist_performance'][metric]) * 1.1]
                )),
            showlegend=False,
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title=f'Playlist Performance by {metric}'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 17: SEO Score
        st.header("Video SEO Scores")
        show_recommendations = st.checkbox("Show SEO Recommendations", value=True)
        
        fig = go.Figure(go.Bar(
            x=mock_data['seo_scores'],
            y=[f"Video {i+1}" for i in range(len(mock_data['seo_scores']))],
            orientation='h',
            marker_color=mock_data['seo_scores'],
            marker_colorscale='Reds',
            text=mock_data['seo_scores'],
            textposition='inside'
        ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title='SEO Scores per Video',
            xaxis_title='SEO Score (0-100)',
            yaxis_title='Video',
            xaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        if show_recommendations:
            st.markdown("""
            <div style="background-color: #212121; padding: 15px; border-radius: 8px; margin-top: 10px;">
                <h4>SEO Recommendations:</h4>
                <ul>
                    <li>Use more specific keywords in your titles</li>
                    <li>Add at least 10 relevant tags to each video</li>
                    <li>Write detailed descriptions with timestamps</li>
                    <li>Create custom thumbnails with readable text</li>
                    <li>Use chapters in your longer videos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Insight 18: Subscriber Gain/Loss Events
        st.header("Subscriber Gain/Loss Events")
        event_date_range = st.date_input(
            "Select Date Range for Events:",
            value=(mock_data['sub_events']['dates'][0], mock_data['sub_events']['dates'][-1])
        )
        
        mask = (pd.to_datetime(mock_data['sub_events']['dates']) >= pd.to_datetime(event_date_range[0])) & \
               (pd.to_datetime(mock_data['sub_events']['dates']) <= pd.to_datetime(event_date_range[1]))
        
        filtered_dates = np.array(mock_data['sub_events']['dates'])[mask]
        filtered_changes = np.array(mock_data['sub_events']['changes'])[mask]
        
        fig = go.Figure()
        
        # Add stems
        for date, change in zip(filtered_dates, filtered_changes):
            color = 'red' if change > 0 else 'darkred'
            fig.add_trace(go.Scatter(
                x=[date, date],
                y=[0, change],
                mode='lines',
                line=dict(color=color, width=2),
                showlegend=False,
                hoverinfo='none'
            ))
        
        # Add markers
        fig.add_trace(go.Scatter(
            x=filtered_dates,
            y=filtered_changes,
            mode='markers',
            marker=dict(
                color=['red' if x > 0 else 'darkred' for x in filtered_changes],
                size=10,
                line=dict(color='white', width=1)
            ),
            hovertemplate='%{x|%b %d}: %{y} subscribers<extra></extra>',
            name='Subscriber Change'
        ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title='Subscriber Gain/Loss Events',
            xaxis_title='Date',
            yaxis_title='Subscriber Change',
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 19: Revenue Estimates
        st.header("Revenue Estimates")
        period = st.selectbox("Select Revenue Period:", ["7 days", "30 days", "90 days", "All time"], index=1)
        
        if period == "7 days":
            days = 7
        elif period == "30 days":
            days = 30
        elif period == "90 days":
            days = 90
        else:
            days = len(mock_data['revenue_dates'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=mock_data['revenue_dates'][-days:],
            y=mock_data['revenue'][-days:],
            line=dict(color='red', width=3),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.2)',
            name='Revenue'
        ))
        
        fig.update_layout(
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='white'),
            title='Estimated Revenue Over Time',
            xaxis_title='Date',
            yaxis_title='Revenue ($)',
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Insight 20: Competitor Comparison
        st.header("Competitor Comparison")
        selected_competitors = st.multiselect(
            "Select Competitors:",
            options=mock_data['competitors'],
            default=mock_data['competitors'][:2]
        )
        
        if not selected_competitors:
            st.warning("Please select at least one competitor")
        else:
            comp_indices = [mock_data['competitors'].index(c) for c in selected_competitors]
            
            fig = go.Figure()
            
            # Add bars for your channel
            fig.add_trace(go.Bar(
                x=['Subscribers', 'Views'],
                y=[channel_data['subscribers'], channel_data['views']],
                name='Your Channel',
                marker_color='red',
                width=0.3
            ))
            
            # Add bars for competitors
            for i, comp_idx in enumerate(comp_indices):
                fig.add_trace(go.Bar(
                    x=['Subscribers', 'Views'],
                    y=[mock_data['comp_subs'][comp_idx], mock_data['comp_views'][comp_idx]],
                    name=mock_data['competitors'][comp_idx],
                    marker_color=px.colors.sequential.Reds[i+2],
                    width=0.3
                ))
            
            fig.update_layout(
                barmode='group',
                plot_bgcolor='#000000',
                paper_bgcolor='#000000',
                font=dict(color='white'),
                title='Channel Comparison',
                yaxis_type='log',
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Run the dashboard
if __name__ == "__main__":
    youtube_dashboard()
