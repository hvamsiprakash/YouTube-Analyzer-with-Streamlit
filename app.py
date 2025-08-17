import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from PIL import Image
import time

# YouTube API setup
API_KEY = "AIzaSyDGV_rw-styH4jKBMRr4fcX2-78jc79D3Q"
BASE_URL = "https://www.googleapis.com/youtube/v3/"

# Page configuration
st.set_page_config(
    page_title="YouTube Creator Dashboard",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for YouTube theme
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #000000;
        color: white;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #121212 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    
    /* Text */
    p, div, span {
        color: white !important;
    }
    
    /* Input widgets */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        background-color: #282828 !important;
        color: white !important;
        border-color: #606060 !important;
    }
    
    /* Cards */
    .css-1aumxhk {
        background-color: #181818 !important;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Tabs */
    .st-b7 {
        background-color: #282828 !important;
    }
    
    /* Selected tab */
    .st-b7 > div:first-child > div:first-child > div {
        background-color: #FF0000 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Mock data generator functions (replace with actual API calls)
def get_channel_stats(channel_id):
    # Simulate API delay
    time.sleep(0.5)
    
    # Mock data - in a real app, you'd call the YouTube API here
    mock_data = {
        'channel_name': 'Tech Reviews',
        'subscribers': 1245873,
        'total_views': 45678921,
        'videos': 342,
        'join_date': '2015-03-15',
        'country': 'United States',
        'thumbnail': 'https://via.placeholder.com/150/FF0000/FFFFFF?text=Channel'
    }
    return mock_data

def get_subscriber_growth(channel_id, period='monthly'):
    # Generate mock growth data
    dates = pd.date_range(end=datetime.today(), periods=12, freq='M').strftime('%Y-%m').tolist()
    growth = np.random.randint(5000, 50000, size=12).cumsum().tolist()
    return pd.DataFrame({'Month': dates, 'Subscribers': growth})

def get_video_performance(channel_id):
    # Mock top 5 videos
    videos = [
        {'title': 'iPhone 15 Pro Review', 'views': 5400000, 'likes': 245000, 'comments': 32000},
        {'title': 'Samsung Galaxy S23 Ultra', 'views': 4800000, 'likes': 198000, 'comments': 28000},
        {'title': 'Google Pixel 8 Pro', 'views': 3900000, 'likes': 187000, 'comments': 24000},
        {'title': 'Best Smartphones 2023', 'views': 3700000, 'likes': 176000, 'comments': 21000},
        {'title': 'MacBook Pro M2 Review', 'views': 3200000, 'likes': 154000, 'comments': 19000}
    ]
    return pd.DataFrame(videos)

def get_audience_demographics(channel_id):
    # Mock demographic data
    gender = {'Male': 68, 'Female': 30, 'Other': 2}
    age = {'13-17': 5, '18-24': 28, '25-34': 42, '35-44': 15, '45-54': 7, '55+': 3}
    countries = {'United States': 42, 'India': 18, 'United Kingdom': 12, 'Canada': 8, 'Germany': 6, 'Other': 14}
    return gender, age, countries

# Dashboard Header
st.title("YouTube Creator Dashboard")
st.markdown("Analyze your channel performance and gain insights to grow your audience")

# Sidebar for inputs
with st.sidebar:
    st.header("Channel Configuration")
    channel_id = st.text_input("Enter YouTube Channel ID", value="UC_x5XG1OV2P6uZZ5FSM9Ttw")
    
    st.header("Display Options")
    time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "Last year"])
    compare_period = st.checkbox("Compare with previous period")
    
    st.header("Insight Selection")
    selected_insights = st.multiselect(
        "Choose insights to display",
        options=[
            "Subscriber Growth", "Video Performance", "Audience Demographics",
            "Engagement Metrics", "Traffic Sources", "Revenue Estimates"
        ],
        default=["Subscriber Growth", "Video Performance", "Audience Demographics"]
    )
    
    st.markdown("---")
    st.markdown("🔴 **Live Analytics**")
    real_time = st.checkbox("Enable real-time updates", value=False)
    if real_time:
        update_freq = st.select_slider("Update frequency", options=["5 min", "15 min", "30 min", "1 hour"])

# Main dashboard layout
col1, col2, col3, col4 = st.columns(4)

# Fetch channel data (mock for now)
channel_data = get_channel_stats(channel_id)

# Key metrics cards
with col1:
    st.metric("Total Subscribers", f"{channel_data['subscribers']:,}", "↑ 12.5% (7d)")
    st.plotly_chart(
        go.Figure(go.Indicator(
            mode="gauge+number",
            value=78,
            title={'text': "Engagement Score"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#FF0000"},
                   'steps': [
                       {'range': [0, 50], 'color': "#282828"},
                       {'range': [50, 80], 'color': "#404040"},
                       {'range': [80, 100], 'color': "#606060"}]
            }
        )).update_layout(
            height=200,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        ),
        use_container_width=True
    )

with col2:
    st.metric("Total Views", f"{channel_data['total_views']:,}", "↑ 8.3% (7d)")
    st.plotly_chart(
        go.Figure(go.Indicator(
            mode="number+delta",
            value=4.7,
            title={'text': "Avg. Video Rating"},
            delta={'reference': 4.5, 'increasing': {'color': "#FF0000"}},
            number={'suffix': " ⭐"}
        )).update_layout(
            height=150,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        ),
        use_container_width=True
    )

with col3:
    st.metric("Total Videos", channel_data['videos'], "↑ 3 (30d)")
    st.plotly_chart(
        go.Figure(go.Indicator(
            mode="number",
            value=24.8,
            title={'text': "Avg. Watch Time (min)"}
        )).update_layout(
            height=150,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        ),
        use_container_width=True
    )

with col4:
    st.metric("Channel Age", f"{(datetime.now() - datetime.strptime(channel_data['join_date'], '%Y-%m-%d')).days // 365} years")
    st.plotly_chart(
        go.Figure(go.Indicator(
            mode="number",
            value=63,
            title={'text': "Retention % (30s)"}
        )).update_layout(
            height=150,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"}
        ),
        use_container_width=True
    )

# Divider
st.markdown("---")

# First row of insights
st.subheader("Channel Performance Overview")
tab1, tab2, tab3 = st.tabs(["Subscriber Growth", "Video Performance", "Audience Insights"])

with tab1:
    # Subscriber growth chart
    growth_data = get_subscriber_growth(channel_id)
    fig = px.line(
        growth_data,
        x='Month',
        y='Subscribers',
        title='Subscriber Growth Trend',
        color_discrete_sequence=['#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis_title='',
        yaxis_title='Subscribers'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Subscriber gain/loss
    st.markdown("#### Subscriber Events")
    event_data = pd.DataFrame({
        'Date': pd.date_range(end=datetime.today(), periods=10).strftime('%Y-%m-%d'),
        'Change': np.random.randint(-500, 1500, size=10)
    })
    fig = px.bar(
        event_data,
        x='Date',
        y='Change',
        color='Change',
        color_continuous_scale=['#FF0000', '#FFFFFF', '#00FF00'],
        title='Daily Subscriber Changes'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Top performing videos
    video_data = get_video_performance(channel_id)
    fig = px.bar(
        video_data,
        x='views',
        y='title',
        orientation='h',
        title='Top Performing Videos by Views',
        color='views',
        color_continuous_scale=['#606060', '#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        yaxis_title='',
        xaxis_title='Views',
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Video upload frequency heatmap
    st.markdown("#### Upload Frequency")
    heatmap_data = pd.DataFrame({
        'Date': pd.date_range(end=datetime.today(), periods=90).strftime('%Y-%m-%d'),
        'Uploads': np.random.poisson(0.3, size=90)
    })
    fig = px.density_heatmap(
        heatmap_data,
        x=pd.to_datetime(heatmap_data['Date']).dt.day_name(),
        y=pd.to_datetime(heatmap_data['Date']).dt.week,
        z='Uploads',
        histfunc="sum",
        title='Video Upload Heatmap (Last 90 Days)',
        color_continuous_scale=['#000000', '#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis_title='Day of Week',
        yaxis_title='Week Number'
    )
    st.plotly_chart(fig, use_container_width=True)



with tab3:
    # Audience demographics
    gender, age, countries = get_audience_demographics(channel_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gender distribution
        fig = px.pie(
            names=list(gender.keys()),
            values=list(gender.values()),
            title='Audience Gender Distribution',
            hole=0.4,
            color_discrete_sequence=['#FF0000', '#990000', '#330000']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white'},
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        # Age distribution
        fig = px.bar(
            x=list(age.values()),
            y=list(age.keys()),
            orientation='h',
            title='Audience Age Distribution',
            color=list(age.values()),
            color_continuous_scale=['#606060', '#FF0000']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white'},
            yaxis_title='',
            xaxis_title='Percentage',
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Country distribution
    st.markdown("#### Audience Geography")
    country_df = pd.DataFrame({
        'Country': list(countries.keys()),
        'Percentage': list(countries.values())
    })
    fig = px.choropleth(
        country_df,
        locations='Country',
        locationmode='country names',
        color='Percentage',
        title='Audience by Country',
        color_continuous_scale=['#000000', '#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        geo=dict(bgcolor='rgba(0,0,0,0)')
    )
    st.plotly_chart(fig, use_container_width=True)

# Second row of insights
st.subheader("Engagement & Performance Metrics")
tab4, tab5, tab6 = st.tabs(["Engagement", "Traffic Sources", "Revenue"])

with tab4:
    # Engagement metrics
    st.markdown("#### Engagement Rate Over Time")
    engagement_data = pd.DataFrame({
        'Date': pd.date_range(end=datetime.today(), periods=30).strftime('%Y-%m-%d'),
        'Likes': np.random.randint(1000, 5000, size=30),
        'Comments': np.random.randint(100, 1000, size=30),
        'Shares': np.random.randint(50, 500, size=30)
    })
    fig = px.area(
        engagement_data,
        x='Date',
        y=['Likes', 'Comments', 'Shares'],
        title='Daily Engagement Metrics',
        color_discrete_sequence=['#FF0000', '#990000', '#330000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis_title='',
        yaxis_title='Count'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Viewer retention
    st.markdown("#### Viewer Retention")
    retention_data = pd.DataFrame({
        'Time (seconds)': range(0, 600, 30),
        'Retention (%)': [100 - x/6 for x in range(0, 600, 30)]
    })
    fig = px.line(
        retention_data,
        x='Time (seconds)',
        y='Retention (%)',
        title='Average Viewer Retention',
        color_discrete_sequence=['#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis_title='Video Duration (seconds)',
        yaxis_title='% of Viewers Remaining'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    # Traffic sources
    st.markdown("#### Traffic Sources Breakdown")
    sources_data = pd.DataFrame({
        'Source': ['YouTube Search', 'Suggested Videos', 'External', 'Playlists', 'Channel Pages'],
        'Percentage': [42, 28, 15, 10, 5]
    })
    fig = px.pie(
        sources_data,
        names='Source',
        values='Percentage',
        title='Where Your Views Come From',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.Reds_r
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Device distribution
    st.markdown("#### Device Distribution")
    device_data = pd.DataFrame({
        'Device': ['Mobile', 'Desktop', 'Tablet', 'TV'],
        'Percentage': [68, 25, 5, 2]
    })
    fig = px.funnel(
        device_data,
        x='Percentage',
        y='Device',
        title='Viewer Devices',
        color_discrete_sequence=['#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        yaxis_title='',
        xaxis_title='Percentage'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab6:
    # Revenue estimates
    st.markdown("#### Estimated Revenue")
    revenue_data = pd.DataFrame({
        'Month': pd.date_range(end=datetime.today(), periods=6, freq='M').strftime('%Y-%m'),
        'Revenue': [1200, 1500, 1800, 2100, 2400, 2700]
    })
    fig = px.line(
        revenue_data,
        x='Month',
        y='Revenue',
        title='Monthly Revenue Trend',
        markers=True,
        color_discrete_sequence=['#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        yaxis_title='Revenue (USD)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # CPM/RPM metrics
    st.markdown("#### Performance Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg. CPM", "$4.25", "↑ $0.15 (30d)")
    with col2:
        st.metric("Avg. RPM", "$3.80", "↑ $0.12 (30d)")
    with col3:
        st.metric("Impressions", "2.4M", "↑ 8.7% (30d)")

# Third row - Additional insights
st.subheader("Advanced Insights")
col1, col2 = st.columns(2)

with col1:
    # Playlist performance
    st.markdown("#### Playlist Performance")
    playlist_data = pd.DataFrame({
        'Playlist': ['Tech Reviews', 'Unboxings', 'Tutorials', 'Comparisons'],
        'Views': [4500000, 3200000, 2800000, 2100000],
        'Avg. Watch %': [65, 58, 72, 61]
    })
    fig = px.scatter(
        playlist_data,
        x='Views',
        y='Avg. Watch %',
        size='Views',
        color='Playlist',
        title='Playlist Engagement',
        color_discrete_sequence=px.colors.sequential.Reds
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # SEO score
    st.markdown("#### Video SEO Score")
    seo_data = pd.DataFrame({
        'Video': ['iPhone 15 Review', 'Samsung S23 Review', 'Pixel 8 Review', 'Best Phones 2023'],
        'SEO Score': [87, 78, 82, 91]
    })
    fig = px.bar(
        seo_data,
        x='SEO Score',
        y='Video',
        orientation='h',
        title='SEO Score by Video',
        color='SEO Score',
        color_continuous_scale=['#606060', '#FF0000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        yaxis_title='',
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Competitor comparison
    st.markdown("#### Competitor Comparison")
    competitor_data = pd.DataFrame({
        'Metric': ['Subscribers', 'Monthly Views', 'Avg. Watch Time', 'Engagement Rate'],
        'Your Channel': [1245873, 4567892, 24.8, 4.7],
        'Competitor A': [987654, 3456789, 22.1, 4.3],
        'Competitor B': [1567890, 5678901, 26.5, 4.9]
    })
    fig = px.bar(
        competitor_data,
        x='Metric',
        y=['Your Channel', 'Competitor A', 'Competitor B'],
        barmode='group',
        title='Channel Comparison',
        color_discrete_sequence=['#FF0000', '#990000', '#330000']
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis_title='',
        yaxis_title='Value'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent comments
    st.markdown("#### Recent Comments")
    comments = [
        {"text": "Great review! Very detailed.", "video": "iPhone 15 Review", "time": "2h ago"},
        {"text": "When will you review the new Pixel?", "video": "Q&A", "time": "5h ago"},
        {"text": "The comparison was really helpful", "video": "S23 vs iPhone", "time": "1d ago"},
        {"text": "Can you do more tutorial videos?", "video": "Android Tips", "time": "2d ago"}
    ]
    
    for comment in comments:
        with st.expander(f"\"{comment['text']}\" - {comment['video']} ({comment['time']})"):
            st.write(f"**Video:** {comment['video']}")
            st.write(f"**Comment:** {comment['text']}")
            col1, col2 = st.columns([3,1])
            with col1:
                st.text_input("Reply to comment", key=f"reply_{comment['text'][:10]}", placeholder="Type your reply...")
            with col2:
                st.button("Send", key=f"send_{comment['text'][:10]}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #AAAAAA;">
    <p>YouTube Creator Dashboard • Data updates every 24 hours • Last updated: {}</p>
    <p>For official YouTube Analytics, visit <a href="https://studio.youtube.com" style="color: #FF0000;">YouTube Studio</a></p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)
