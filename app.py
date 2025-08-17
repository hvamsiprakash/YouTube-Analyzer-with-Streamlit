import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

API_KEY = "AIzaSyDGV_rw-styH4jKBMRr4fcX2-78jc79D3Q"
BASE_URL = "https://www.googleapis.com/youtube/v3/"
st.set_page_config(page_title="YouTube Creator Dashboard", layout="wide")

# YOUTUBE THEME
st.markdown("""
<style>
.stApp { background:#000;color:#fff; }
h1,h2,h3,h4,h5,h6 { color:#fff!important; }
[data-testid=stSidebar] { background:#121212!important; }
.stTextInput input, .stSelectbox select { background:#282828!important; color:#fff!important; }
</style>
""", unsafe_allow_html=True)

# ----------- API FETCHERS ----------- #
def get_channel_info(cid):
    url = f"{BASE_URL}channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}"
    res = requests.get(url).json()
    if "items" in res and len(res["items"]) > 0:
        item = res["items"]
        # get uploads playlist ID
        uploads_playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]
        return {
            "name":item["snippet"]["title"],
            "desc":item["snippet"]["description"],
            "country":item["snippet"].get("country",""),
            "avatar":item["snippet"]["thumbnails"]["high"]["url"],
            "created":item["snippet"]["publishedAt"][:10],
            "subscribers":int(item["statistics"].get("subscriberCount",0)),
            "views":int(item["statistics"].get("viewCount",0)),
            "videos":int(item["statistics"].get("videoCount",0)),
            "uploads":uploads_playlist
        }
    return None

def get_uploads_videos(playlist_id, max_results=200):
    # Will paginate until all (or max_results) are fetched
    vids, token = [], None
    while len(vids) < max_results:
        url = f"{BASE_URL}playlistItems?part=snippet&playlistId={playlist_id}&maxResults=50&key={API_KEY}"
        if token: url += f"&pageToken={token}"
        res = requests.get(url).json()
        for i in res.get("items",[]):
            snip = i["snippet"]
            vids.append({
                "video_id":snip["resourceId"]["videoId"],
                "title":snip["title"],
                "published":snip["publishedAt"][:10],
                "desc":snip.get("description","")
            })
        token = res.get("nextPageToken",None)
        if not token: break
    return pd.DataFrame(vids)

def get_video_metrics(ids):
    all_stats, step = [], 50
    ids = ids[:400] # limit for demo/production quota
    for i in range(0,len(ids),step):
        batch = ",".join(ids[i:i+step])
        url = f"{BASE_URL}videos?part=snippet,statistics,contentDetails&id={batch}&key={API_KEY}"
        res = requests.get(url).json()
        for item in res.get("items",[]):
            stats = item["statistics"]
            snip = item["snippet"]
            duration = item["contentDetails"]["duration"]
            # Convert ISO 8601 (PT4M30S) to seconds:
            def iso_duration(iso):
                import re
                m = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?',iso)
                return int(m.group(1) or 0)*60 + int(m.group(2) or 0)
            return_dict = {
                "video_id":item["id"],
                "title":snip["title"],
                "published":snip["publishedAt"][:10],
                "views":int(stats.get("viewCount",0)),
                "likes":int(stats.get("likeCount",0)),
                "comments":int(stats.get("commentCount",0)),
                "duration":iso_duration(duration),
                "tags": "|".join(snip.get("tags",[]))
            }
            all_stats.append(return_dict)
    return pd.DataFrame(all_stats)

def get_playlists(cid):
    url = f"{BASE_URL}playlists?part=snippet,contentDetails&channelId={cid}&maxResults=30&key={API_KEY}"
    pl = []
    res = requests.get(url).json()
    for i in res.get("items",[]):
        pl.append({
            "title":i["snippet"]["title"],
            "video_count":i["contentDetails"]["itemCount"],
            "desc":i["snippet"]["description"]
        })
    return pd.DataFrame(pl)

def get_comments(video_id, max_results=20):
    try:
        url = f"{BASE_URL}commentThreads?part=snippet&videoId={video_id}&maxResults={max_results}&key={API_KEY}"
        res = requests.get(url).json()
        comments = []
        for i in res.get("items",[]):
            cm = i["snippet"]["topLevelComment"]["snippet"]
            comments.append({"author":cm["authorDisplayName"],"text":cm["textDisplay"],"time":cm["publishedAt"][:10]})
        return comments
    except: return []

def get_competitor_channels(qry):
    url = f"{BASE_URL}search?part=snippet&type=channel&q={qry}&maxResults=2&key={API_KEY}"
    res = requests.get(url).json()
    return [{"id":i["id"]["channelId"],"name":i["snippet"]["title"]} for i in res.get("items",[])]

# ----------- SIDEBAR FILTERS ----------- #
with st.sidebar:
    st.header("YouTube Channel Analytics")
    channel_id = st.text_input("Channel ID",value="UC_x5XG1OV2P6uZZ5FSM9Ttw")
    date_slider = st.selectbox("Filter Videos By Date", ["All","Last 7 days","Last 30 days","Last 90 days","Last Year"])
    sort_by = st.selectbox("Sort Videos",["views","likes","comments","duration","published"])
    keyword = st.text_input("Search keyword (title/desc/tag)","")
    playlist_filter = st.checkbox("Show Playlists Table")
    show_comments = st.checkbox("Show Latest Comments")
    show_competitors = st.checkbox("Show Competitor Stats")

# ----------- MAIN DASHBOARD BODY ----------- #
info = get_channel_info(channel_id)
if not info:
    st.error("Channel not found or not public. Check the ID and try again.")
    st.stop()

# ---- Channel Overview ----
st.image(info["avatar"],width=120)
st.title(f"{info['name']} - YouTube Dashboard")
cols = st.columns(4)
cols[0].metric("Subscribers",f"{info['subscribers']:,}")
cols[1].metric("Views",f"{info['views']:,}")
cols[2].metric("Uploaded Videos",f"{info['videos']:,}")
cols[3].metric("Created",info["created"])
st.markdown(f"<span style='color:#888'>Country: {info['country']}</span>", unsafe_allow_html=True)
st.markdown("---")
st.write(f"**Description:** {info['desc']}")

# ---- Fetch all public uploads ----
uploads_df = get_uploads_videos(info["uploads"], max_results=200)
if len(uploads_df)==0:
    st.error("No public uploads found. Are all videos private/unlisted?")
    st.stop()

# ---- Apply filters ----
vids_df = uploads_df
if date_slider!="All":
    days = {"Last 7 days":7, "Last 30 days":30, "Last 90 days":90, "Last Year":365}[date_slider]
    cutoff = (datetime.now()-pd.Timedelta(days))
    vids_df = vids_df[vids_df['published']>=cutoff.strftime("%Y-%m-%d")]
if keyword.strip():
    pattern = keyword.lower()
    vids_df = vids_df[
        vids_df["title"].str.lower().str.contains(pattern)
        | vids_df["desc"].str.lower().str.contains(pattern)
    ]

if len(vids_df)==0:
    st.warning("No videos match filter.")
else:
    # ---- Get stats for videos ----
    stats_df = get_video_metrics(vids_df["video_id"].tolist())
    stats_df = stats_df.sort_values(by=sort_by,ascending=False)
    st.markdown("### Uploaded Videos Table")
    st.dataframe(stats_df[["title","published","views","likes","comments","duration"]].head(50),use_container_width=True)

    # Insights: top charts
    st.markdown("### Unique Charts & Insights")
    tabv1,tabv2,tabv3,tabv4 = st.tabs(["Top Videos","Frequency","Ratios","Trends"])
    with tabv1:
        st.subheader("Top 5: Views / Likes / Comments")
        f1 = px.bar(stats_df.head(5),x="views",y="title",color="views",orientation="h",color_continuous_scale=["#900","#FF0000"])
        f1.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(f1,use_container_width=True)
        f2 = px.bar(stats_df.head(5),x="likes",y="title",color="likes",orientation="h",color_continuous_scale=["#c00","#FF0000"])
        f2.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(f2,use_container_width=True)
        f3 = px.bar(stats_df.head(5),x="comments",y="title",color="comments",orientation="h",color_continuous_scale=["#f33","#FF0000"])
        f3.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(f3,use_container_width=True)

    with tabv2:
        st.subheader("Upload Frequency by Month")
        months = pd.to_datetime(stats_df['published']).dt.to_period('M')
        month_counts = months.value_counts().sort_index()
        fig = px.bar(x=month_counts.index.astype(str),y=month_counts.values,
                     labels={'x':'Month','y':'Uploads'},
                     color=month_counts.values, color_continuous_scale=["#660000","#FF0000"], title="Uploads / Month")
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)

        st.subheader("Upload Frequency by Weekday")
        weekdays = pd.to_datetime(stats_df['published']).dt.day_name()
        day_counts = weekdays.value_counts()
        fig2 = px.bar(x=day_counts.index,y=day_counts.values,
                     labels={'x':'Weekday','y':'Uploads'},
                     color=day_counts.values, color_continuous_scale=["#900","#FF0000"], title="Uploads / Weekday")
        fig2.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig2,use_container_width=True)

    with tabv3:
        st.subheader("Like-View Ratio (per video)")
        stats_df["like_view_ratio"] = stats_df["likes"]/stats_df["views"].replace(0,1)
        fig = px.scatter(stats_df.head(50),x="views",y="likes",size="like_view_ratio",color="like_view_ratio",title="Like/View Ratio", color_continuous_scale=["#FF0000","#c00"])
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)
        
        st.subheader("Comment-View Ratio (per video)")
        stats_df["comment_view_ratio"] = stats_df["comments"]/stats_df["views"].replace(0,1)
        fig2 = px.scatter(stats_df.head(50),x="views",y="comments",size="comment_view_ratio",color="comment_view_ratio",title="Comment/View Ratio", color_continuous_scale=["#FF0000","#f33"])
        fig2.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig2,use_container_width=True)
    
    with tabv4:
        st.subheader("Views, Likes, Comments Trend")
        fig = px.line(stats_df.sort_values("published"),x="published",y=["views","likes","comments"],markers=True,
                      color_discrete_map={"views":"#FF0000","likes":"#900","comments":"#c33"})
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)

        st.subheader("Video Duration Histogram")
        fig2 = px.histogram(stats_df, x="duration", nbins=20, color="duration", color_continuous_scale=["#f33","#FF0000"], title="Video Duration Distribution")
        fig2.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig2,use_container_width=True)

    # Advanced: Keyword/Tag Frequency (word cloud possible)
    if "tags" in stats_df:
        tags = stats_df["tags"].str.cat(sep="|").split("|")
        tag_counts = pd.Series(tags).value_counts().head(20)
        fig = px.bar(x=tag_counts.index,y=tag_counts.values,color=tag_counts.values,
                     color_continuous_scale=["#900","#FF0000"],title="Most Used Keywords/Tags")
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)

    # 'Viral' Video Card: most views in X days
    viral_df = stats_df[stats_df['published']>(datetime.now()-pd.Timedelta(7)).strftime("%Y-%m-%d")]
    if not viral_df.empty:
        top_viral = viral_df[viral_df["views"]==viral_df["views"].max()]
        st.markdown(f"#### 🚀 Viral Video (Last 7 days): <span style='color:#FF0000'>{top_viral['title'].iloc[0]}</span>",unsafe_allow_html=True)
        st.metric("Views",f"{top_viral['views'].iloc:,}")

# ---- Playlists ----
if playlist_filter:
    pl_df = get_playlists(channel_id)
    if len(pl_df)>0:
        st.markdown("### Playlists Table")
        st.dataframe(pl_df,use_container_width=True)
        fig = px.bar(pl_df,x="title",y="video_count",color="video_count",color_continuous_scale=["#900","#FF0000"])
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)

# ---- Recent Comments ----
if show_comments:
    st.markdown("### Recent Comments")
    for i in stats_df.head(2)["video_id"]:
        cs = get_comments(i,max_results=5)
        for c in cs:
            st.markdown(f"<div style='background:#181818;color:#fff;border-left:5px solid #FF0000;margin:5px 0;padding:5px 15px;border-radius:8px'><b>{c['author']}</b>: {c['text']}<br><span style='color:#ccc'>{c['time']}</span></div>",unsafe_allow_html=True)

# ---- Competitor stats ----
if show_competitors:
    st.markdown("### Competitor Channel Comparison")
    comp_list = get_competitor_channels(info["name"])
    comp_stats = []
    for c in comp_list:
        cdata = get_channel_info(c["id"])
        if cdata: comp_stats.append(cdata)
    if comp_stats:
        df = pd.DataFrame({
            "Metric":["Subscribers","Views","Videos"],
            info["name"]:[info["subscribers"],info["views"],info["videos"]],
            comp_stats["name"]:[comp_stats["subscribers"],comp_stats["views"],comp_stats["videos"]],
            comp_stats[1]["name"]:[comp_stats[1]["subscribers"],comp_stats[1]["views"],comp_stats[1]["videos"]]
        })
        fig = px.bar(df,x="Metric",y=df.columns[1:],barmode="group",color_discrete_sequence=["#FF0000","#c00","#900"])
        fig.update_layout(paper_bgcolor="#000", plot_bgcolor="#000", font=dict(color="white"))
        st.plotly_chart(fig,use_container_width=True)

st.markdown("---")
st.markdown(f"<div style='text-align:center;color:#AAAAAA;'>Enhanced by YouTube Data API v3 • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>",unsafe_allow_html=True)
