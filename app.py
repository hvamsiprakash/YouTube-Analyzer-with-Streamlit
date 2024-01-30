# # Importing necessary libraries and modules
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from wordcloud import WordCloud
# from textblob import TextBlob

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         channel_info = response.get("items", [])[0]["snippet"]
#         statistics_info = response.get("items", [])[0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         published_at = channel_info.get("publishedAt", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))
#         total_likes = int(statistics_info.get("likeCount", 0))
#         total_comments = int(statistics_info.get("commentCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))
#             comments = int(statistics_info.get("commentCount", 0))

#             video_details.append((title, views, likes, comments, url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=5):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="relevance"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             views = item["snippet"]["viewCount"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             likes = int(statistics_info.get("likeCount", 0))

#             video_details.append((title, views, likes, url))

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to generate word cloud from comments
# def generate_word_cloud(comments):
#     try:
#         if not comments:
#             st.warning("No comments to generate a word cloud.")
#             return None

#         text = " ".join(comments)
#         wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

#         return wordcloud
#     except Exception as e:
#         st.error(f"Error generating word cloud: {e}")
#         return None

# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'] += 1
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'] += 1
#             else:
#                 categorized_comments['Negative'] += 1

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

# # Main Streamlit app
# st.title("YouTube Analyzer")

# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="YOUR_CHANNEL_ID")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Published At:** {published_at}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")
#         st.write(f"**Total Likes:** {total_likes}")
#         st.write(f"**Total Comments:** {total_comments}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Advanced Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
#         fig_views.update_layout(height=400, width=800)
#         st.plotly_chart(fig_views)

#         # Bar Chart for Likes and Comments
#         fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
#                                     title="Bar Chart for Likes and Comments", barmode="group")
#         fig_likes_comments.update_layout(height=400, width=800)
#         st.plotly_chart(fig_likes_comments)

#         # Additional: Polarity Chart for Comments
#         categorized_comments = analyze_and_categorize_comments(videos_df["Comments"].apply(str))
#         fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
#                               labels={'x': 'Sentiment', 'y': 'Count'},
#                               title="Sentiment Distribution of Comments")
#         fig_polarity.update_layout(height=400, width=800)
#         st.plotly_chart(fig_polarity)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         # videos_df['URL'] = videos_df['URL'].apply(lambda x: f'<a href="{x}" target="_blank">Link</a>')
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: x)
#         st.write(videos_df, unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="Python Tutorial")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=5)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**Title:** {video[0]}")
#             st.write(f"**Views:** {video[1]}, **URL:** {video[2]}")
#             thumbnail_url = f"https://img.youtube.com/vi/{video[2].split('=')[1]}/default.jpg"
#             st.image(thumbnail_url, caption=f"Video URL: {video[2]}", use_container_width=True)
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization and Word Cloud
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

#     if st.sidebar.button("Analyze Sentiments and Generate Word Cloud"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Generate Word Cloud
#         wordcloud = generate_word_cloud(comments_sentiment)
#         if wordcloud is not None:
#             st.subheader("Word Cloud")
#             st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)

#             # Analyze and Categorize Comments
#             categorized_comments = analyze_and_categorize_comments(comments_sentiment)

#             # Display Sentimental Analysis Results
#             st.subheader("Sentimental Analysis Results")
#             for sentiment, count in categorized_comments.items():
#                 st.write(f"**{sentiment} Sentiments:** {count}")

# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
#     "[GitHub](https://github.com/your-github-profile)"
# )

# # Importing necessary libraries and modules
# import matplotlib.pyplot as plt
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from wordcloud import WordCloud
# from textblob import TextBlob

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         if "items" not in response or not response["items"]:
#             st.error("No channel found with the provided ID.")
#             return None, None, None, None, None, None, None, None, None

#         channel_info = response["items"][0]["snippet"]
#         statistics_info = response["items"][0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         published_at = channel_info.get("publishedAt", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))
#         total_likes = int(statistics_info.get("likeCount", 0))
#         total_comments = int(statistics_info.get("commentCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))
#             comments = int(statistics_info.get("commentCount", 0))

#             video_details.append((title, views, likes, comments, url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=5):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="relevance"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))

#             video_details.append((title, views, likes, url))

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to generate word cloud from comments
# def generate_word_cloud(comments):
#     try:
#         if not comments:
#             st.warning("No comments to generate a word cloud.")
#             return None

#         text = " ".join(comments)

#         # Generate WordCloud
#         wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

#         # Display WordCloud using matplotlib
#         st.subheader("Word Cloud")
#         st.image(wordcloud.to_image(), caption="Generated Word Cloud", use_container_width=True)
#     except Exception as e:
#         st.error(f"Error generating word cloud: {e}")






# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'] += 1
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'] += 1
#             else:
#                 categorized_comments['Negative'] += 1

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

# # Main Streamlit app
# st.title("YouTube Analyzer")

# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID", value="YOUR_CHANNEL_ID")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Published At:** {published_at}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")
#         st.write(f"**Total Likes:** {total_likes}")
#         st.write(f"**Total Comments:** {total_comments}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Advanced Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
#         fig_views.update_layout(height=400, width=800)
#         st.plotly_chart(fig_views)

#         # Bar Chart for Likes and Comments
#         fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
#                                     title="Bar Chart for Likes and Comments", barmode="group")
#         fig_likes_comments.update_layout(height=400, width=800)
#         st.plotly_chart(fig_likes_comments)

#         # Additional: Polarity Chart for Comments
#         categorized_comments = analyze_and_categorize_comments(videos_df["Comments"].apply(str))
#         fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
#                               labels={'x': 'Sentiment', 'y': 'Count'},
#                               title="Sentiment Distribution of Comments")
#         fig_polarity.update_layout(height=400, width=800)
#         st.plotly_chart(fig_polarity)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: x)
#         st.write(videos_df, unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="Python Tutorial")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=5)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**Title:** {video[0]}")
#             st.write(f"**Views:** {video[1]}, **Likes:** {video[2]}, **URL:** {video[3]}")
#             thumbnail_url = f"https://img.youtube.com/vi/{video[3].split('=')[1]}/default.jpg"
#             st.image(thumbnail_url, caption=f"Video URL: {video[3]}")
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization and Word Cloud
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

#     # Allow the user to choose the type of comments
#     selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

#     if st.sidebar.button("Analyze Sentiments and Generate Word Cloud"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Filter comments based on the selected sentiment
#         if selected_sentiment == "Positive":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity > 0]
#         elif selected_sentiment == "Neutral":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity == 0]
#         else:
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity < 0]

#         # Display Advanced Visualization Charts for Comments
#         st.subheader(f"{selected_sentiment.capitalize()} Comments Analysis")
#         categorized_comments = analyze_and_categorize_comments(filtered_comments)

#         # Display Sentimental Analysis Results
#         for sentiment, count in categorized_comments.items():
#             st.write(f"**{sentiment} Sentiments:** {count}")

#         # Generate and Display Word Cloud
#         wordcloud = generate_word_cloud(filtered_comments)
#         if wordcloud is not None:
#             st.subheader("Word Cloud")
#             st.image(wordcloud.to_image(), caption="Generated Word Cloud")


# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
#     "[GitHub](https://github.com/your-github-profile)"
# )


# # Importing necessary libraries and modules
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from textblob import TextBlob

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         channel_info = response.get("items", [])[0]["snippet"]
#         statistics_info = response.get("items", [])[0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         published_at = channel_info.get("publishedAt", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))
#         total_likes = int(statistics_info.get("likeCount", 0))
#         total_comments = int(statistics_info.get("commentCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))
#             comments = int(statistics_info.get("commentCount", 0))

#             video_details.append((title, views, likes, comments, url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=5):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="relevance"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))

#             video_details.append((title, views, likes, url))

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'] += 1
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'] += 1
#             else:
#                 categorized_comments['Negative'] += 1

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

# # Main Streamlit app
# st.title("YouTube Analyzer")

# # Description of the YouTube Analyzer app
# st.markdown(
#     """
#     Welcome to YouTube Analyzer – your go-to tool for in-depth analysis of YouTube channels and videos! 
#     Whether you want to explore detailed analytics for a specific channel, discover top-notch video recommendations, 
#     or dive into the sentiment analysis of video comments, this app provides a comprehensive and interactive experience. 
#     Gain insights into channel statistics, explore engaging charts, and uncover the sentiment behind the comments. 
#     Let's unravel the world of YouTube together!
#     """
# )

# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="YOUR_CHANNEL_ID")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Published At:** {published_at}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")
#         st.write(f"**Total Likes:** {total_likes}")
#         st.write(f"**Total Comments:** {total_comments}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Advanced Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
#         fig_views.update_layout(height=400, width=800)
#         st.plotly_chart(fig_views)

#         # Bar Chart for Likes and Comments
#         fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
#                                     title="Bar Chart for Likes and Comments", barmode="group")
#         fig_likes_comments.update_layout(height=400, width=800)
#         st.plotly_chart(fig_likes_comments)

#         # Additional: Polarity Chart for Comments
#         categorized_comments = analyze_and_categorize_comments(videos_df["Comments"].apply(str))
#         fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
#                               labels={'x': 'Sentiment', 'y': 'Count'},
#                               title="Sentiment Distribution of Comments")
#         fig_polarity.update_layout(height=400, width=800)
#         st.plotly_chart(fig_polarity)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: x)
#         st.write(videos_df, unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=5)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**Title:** {video[0]}")
#             st.write(f"**Views:** {video[1]}, **Likes:** {video[2]}, **URL:** {video[3]}")
#             thumbnail_url = f"https://img.youtube.com/vi/{video[3].split('=')[1]}/default.jpg"
#             st.image(thumbnail_url, caption=f"Video URL: {video[3]}")
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

#     # Allow the user to choose the type of comments
#     selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

#     if st.sidebar.button("Analyze Sentiments"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Filter comments based on the selected sentiment
#         if selected_sentiment == "Positive":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity > 0]
#         elif selected_sentiment == "Neutral":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity == 0]
#         else:
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity < 0]

#         # Display Advanced Visualization Charts for Comments
#         st.subheader(f"{selected_sentiment.capitalize()} Comments Analysis")

#         # Additional: Dynamic Visualization Charts based on the type of comments
#         if filtered_comments:
#             # You can customize and add more charts as needed
#             # For example, let's add a bar chart for the length of comments
#             comments_df = pd.DataFrame({"Comments": filtered_comments})
#             comments_df['Length'] = comments_df['Comments'].apply(len)

#             fig_length_distribution = px.histogram(comments_df, x='Length', title='Comment Length Distribution',
#                                                    labels={'Length': 'Comment Length'})
#             st.plotly_chart(fig_length_distribution)

#             # Additional: Display DataFrame of comments
#             st.subheader("All Comments")
#             st.write(comments_df)


# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
#     "[GitHub](https://github.com/your-github-profile)"
# )



# # Importing necessary libraries and modules
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from textblob import TextBlob
# from wordcloud import WordCloud
# import matplotlib.pyplot as plt

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         channel_info = response.get("items", [])[0]["snippet"]
#         statistics_info = response.get("items", [])[0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         published_at = channel_info.get("publishedAt", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))
#         total_likes = int(statistics_info.get("likeCount", 0))
#         total_comments = int(statistics_info.get("commentCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))
#             comments = int(statistics_info.get("commentCount", 0))

#             video_details.append((title, views, likes, comments, url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Views", "Likes", "Comments", "URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Views", "Likes", "Comments", "URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=5):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="relevance"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             views = int(statistics_info.get("viewCount", 0))
#             likes = int(statistics_info.get("likeCount", 0))

#             video_details.append((title, views, likes, url))

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to generate word cloud from comments
# def generate_word_cloud(comments):
#     try:
#         text = ' '.join(comments)
#         wordcloud = WordCloud(width=800, height=400, random_state=21, max_font_size=110, background_color='white').generate(text)
#         return wordcloud
#     except Exception as e:
#         st.error(f"Error generating word cloud: {e}")
#         return None

# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': 0, 'Neutral': 0, 'Negative': 0}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'] += 1
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'] += 1
#             else:
#                 categorized_comments['Negative'] += 1

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': 0, 'Neutral': 0, 'Negative': 0}

# # Main Streamlit app
# st.title("YouTube Analyzer")

# # Description of the YouTube Analyzer app
# st.markdown(
#     """
#     Welcome to YouTube Analyzer – your go-to tool for in-depth analysis of YouTube channels and videos! 
#     Whether you want to explore detailed analytics for a specific channel, discover top-notch video recommendations, 
#     or dive into the sentiment analysis of video comments, this app provides a comprehensive and interactive experience. 
#     Gain insights into channel statistics, explore engaging charts, and uncover the sentiment behind the comments. 
#     Let's unravel the world of YouTube together!
#     """
# )

# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="YOUR_CHANNEL_ID")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, published_at, country, total_videos, total_views, total_likes, total_comments, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Published At:** {published_at}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")
#         st.write(f"**Total Likes:** {total_likes}")
#         st.write(f"**Total Comments:** {total_comments}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Advanced Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
#         fig_views.update_layout(height=400, width=800)
#         st.plotly_chart(fig_views)

#         # Bar Chart for Likes and Comments
#         fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
#                                     title="Bar Chart for Likes and Comments", barmode="group")
#         fig_likes_comments.update_layout(height=400, width=800)
#         st.plotly_chart(fig_likes_comments)

#         # Additional: Polarity Chart for Comments
#         categorized_comments = analyze_and_categorize_comments(videos_df["Comments"].apply(str))
#         fig_polarity = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
#                               labels={'x': 'Sentiment', 'y': 'Count'},
#                               title="Sentiment Distribution of Comments")
#         fig_polarity.update_layout(height=400, width=800)
#         st.plotly_chart(fig_polarity)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: x)
#         st.write(videos_df, unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=5)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**Title:** {video[0]}")
#             st.write(f"**Views:** {video[1]}, **Likes:** {video[2]}, **URL:** {video[3]}")
#             thumbnail_url = f"https://img.youtube.com/vi/{video[3].split('=')[1]}/default.jpg"
#             st.image(thumbnail_url, caption=f"Video URL: {video[3]}")
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

#     # Allow the user to choose the type of comments
#     selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

#     if st.sidebar.button("Analyze Sentiments"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Filter comments based on the selected sentiment
#         if selected_sentiment == "Positive":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity > 0]
#         elif selected_sentiment == "Neutral":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity == 0]
#         else:
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity < 0]

#         # Display Advanced Visualization Charts for Comments
#         st.subheader(f"{selected_sentiment.capitalize()} Comments Analysis")

#         # Additional: Dynamic Visualization Charts based on the type of comments
#         if filtered_comments:
#             # Chart 1: Comment Length Distribution
#             comments_df = pd.DataFrame({"Comments": filtered_comments})
#             comments_df['Length'] = comments_df['Comments'].apply(len)
#             fig_length_distribution = px.histogram(comments_df, x='Length', title='Comment Length Distribution',
#                                                    labels={'Length': 'Comment Length'})
#             st.plotly_chart(fig_length_distribution)

#             # Chart 2: Word Cloud
#             st.subheader(f"Word Cloud for {selected_sentiment.capitalize()} Comments")
#             wordcloud = generate_word_cloud(filtered_comments)
#             if wordcloud:
#                 plt.figure(figsize=(10, 5))
#                 plt.imshow(wordcloud, interpolation='bilinear')
#                 plt.axis('off')
#                 st.pyplot(plt)

#             # Chart 3: Sentiment Polarity Distribution
#             categorized_comments = analyze_and_categorize_comments(filtered_comments)
#             fig_polarity_distribution = px.bar(x=list(categorized_comments.keys()), y=list(categorized_comments.values()),
#                                                labels={'x': 'Sentiment', 'y': 'Count'},
#                                                title=f"{selected_sentiment.capitalize()} Sentiment Distribution")
#             fig_polarity_distribution.update_layout(height=400, width=800)
#             st.plotly_chart(fig_polarity_distribution)

# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
#     "[GitHub](https://github.com/your-github-profile)"
# )










# # Importing necessary libraries and modules
# import streamlit as st
# import googleapiclient.discovery
# import pandas as pd
# import plotly.express as px
# from textblob import TextBlob
# from wordcloud import WordCloud
# import matplotlib.pyplot as plt

# # Set your YouTube Data API key here
# YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# # Initialize the YouTube Data API client
# youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# # Function to get channel analytics
# def get_channel_analytics(channel_id):
#     try:
#         response = youtube.channels().list(
#             part="snippet,statistics",
#             id=channel_id
#         ).execute()

#         channel_info = response.get("items", [])[0]["snippet"]
#         statistics_info = response.get("items", [])[0]["statistics"]

#         channel_title = channel_info.get("title", "N/A")
#         description = channel_info.get("description", "N/A")
#         published_at = channel_info.get("publishedAt", "N/A")
#         country = channel_info.get("country", "N/A")

#         total_videos = int(statistics_info.get("videoCount", 0))
#         total_views = int(statistics_info.get("viewCount", 0))

#         # Fetch all video details for the dataframe
#         videos_df = get_all_video_details(channel_id)

#         return channel_title, description, published_at, country, total_videos, total_views, videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching channel analytics: {e}")
#         return None, None, None, None, None, None, None

# # Function to fetch all video details for a channel
# def get_all_video_details(channel_id):
#     try:
#         response = youtube.search().list(
#             channelId=channel_id,
#             type="video",
#             part="id,snippet",
#             maxResults=50
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics,snippet",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             snippet_info = video_info.get("items", [])[0]["snippet"]
#             views = int(statistics_info.get("viewCount", 0))
#             duration = snippet_info.get("duration", "N/A")
#             upload_date = snippet_info.get("publishedAt", "N/A")
#             channel_name = snippet_info.get("channelTitle", "N/A")
#             thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")

#             video_details.append((title, video_id, views, duration, upload_date, channel_name, url, thumbnail_url))

#         videos_df = pd.DataFrame(video_details, columns=["Title", "Video ID", "Views", "Duration", "Upload Date", "Channel", "URL", "Thumbnail URL"])
#         return videos_df
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video details: {e}")
#         return pd.DataFrame(columns=["Title", "Video ID", "Views", "Duration", "Upload Date", "Channel", "URL", "Thumbnail URL"])

# # Function to get video recommendations based on user's topic
# def get_video_recommendations(topic, max_results=10):
#     try:
#         response = youtube.search().list(
#             q=topic,
#             type="video",
#             part="id,snippet",
#             maxResults=max_results,
#             order="viewCount"
#         ).execute()

#         video_details = []
#         for item in response.get("items", []):
#             video_id = item["id"]["videoId"]
#             title = item["snippet"]["title"]
#             url = f"https://www.youtube.com/watch?v={video_id}"

#             # Use a separate request to get video statistics
#             video_info = youtube.videos().list(
#                 part="statistics,snippet",
#                 id=video_id
#             ).execute()

#             statistics_info = video_info.get("items", [])[0]["statistics"]
#             snippet_info = video_info.get("items", [])[0]["snippet"]
#             views = int(statistics_info.get("viewCount", 0))
#             upload_date = snippet_info.get("publishedAt", "N/A")
#             channel_name = snippet_info.get("channelTitle", "N/A")
#             thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")

#             video_details.append((title, video_id, views, upload_date, channel_name, url, thumbnail_url))

#         return video_details
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching video recommendations: {e}")
#         return None

# # Function to get video comments
# def get_video_comments(video_id):
#     try:
#         comments = []
#         results = youtube.commentThreads().list(
#             part="snippet",
#             videoId=video_id,
#             textFormat="plainText",
#             maxResults=100
#         ).execute()

#         while "items" in results:
#             for item in results["items"]:
#                 comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
#                 comments.append(comment)

#             # Get the next set of results
#             if "nextPageToken" in results:
#                 results = youtube.commentThreads().list(
#                     part="snippet",
#                     videoId=video_id,
#                     textFormat="plainText",
#                     pageToken=results["nextPageToken"],
#                     maxResults=100
#                 ).execute()
#             else:
#                 break

#         return comments
#     except googleapiclient.errors.HttpError as e:
#         st.error(f"Error fetching comments: {e}")
#         return []

# # Function to generate word cloud from comments
# def generate_word_cloud(comments):
#     try:
#         text = ' '.join(comments)
#         wordcloud = WordCloud(width=800, height=400, random_state=21, max_font_size=110, background_color='white').generate(text)
#         return wordcloud
#     except Exception as e:
#         st.error(f"Error generating word cloud: {e}")
#         return None

# # Function to analyze and categorize comments sentiment
# def analyze_and_categorize_comments(comments):
#     try:
#         categorized_comments = {'Positive': [], 'Neutral': [], 'Negative': []}

#         for comment in comments:
#             analysis = TextBlob(comment)
#             # Classify the polarity of the comment
#             if analysis.sentiment.polarity > 0:
#                 categorized_comments['Positive'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
#             elif analysis.sentiment.polarity == 0:
#                 categorized_comments['Neutral'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
#             else:
#                 categorized_comments['Negative'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))

#         return categorized_comments
#     except Exception as e:
#         st.error(f"Error analyzing comments: {e}")
#         return {'Positive': [], 'Neutral': [], 'Negative': []}

# # Main Streamlit app
# st.title("YouTube Analyzer")

# # Description of the YouTube Analyzer app
# st.markdown(
#     """
#     Welcome to YouTube Analyzer – your go-to tool for in-depth analysis of YouTube channels and videos! 
#     Whether you want to explore detailed analytics for a specific channel, discover top-notch video recommendations, 
#     or dive into the sentiment analysis of video comments, this app provides a comprehensive and interactive experience. 
#     Gain insights into channel statistics, explore engaging charts, and uncover the sentiment behind the comments. 
#     Let's unravel the world of YouTube together!
#     """
# )

# # Sidebar
# st.sidebar.title("YouTube Analyzer")
# st.sidebar.subheader("Select a Task")

# # Task 1: Channel Analytics
# if st.sidebar.checkbox("Channel Analytics"):
#     st.sidebar.subheader("Channel Analytics")
#     channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="YOUR_CHANNEL_ID")

#     if st.sidebar.button("Get Channel Analytics"):
#         channel_title, description, published_at, country, total_videos, total_views, videos_df = get_channel_analytics(channel_id_analytics)

#         # Display Channel Overview
#         st.subheader("Channel Overview")
#         st.write(f"**Channel Title:** {channel_title}")
#         st.write(f"**Description:** {description}")
#         st.write(f"**Published At:** {published_at}")
#         st.write(f"**Country:** {country}")
#         st.write(f"**Total Videos:** {total_videos}")
#         st.write(f"**Total Views:** {total_views}")

#         # Advanced Charts for Channel Analytics
#         st.subheader("Advanced Analytics Charts")

#         # Time Series Chart for Views
#         fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
#         fig_views.update_layout(height=400, width=800)
#         st.plotly_chart(fig_views)

#         # Additional: Display DataFrame of video details with clickable URLs
#         st.subheader("All Video Details")
#         videos_df['URL'] = videos_df['URL'].apply(lambda x: f"<a href='{x}' target='_blank'>{x}</a>")
#         st.write(videos_df.to_html(escape=False), unsafe_allow_html=True)

# # Task 2: Video Recommendation based on User's Topic of Interest
# if st.sidebar.checkbox("Video Recommendation"):
#     st.sidebar.subheader("Video Recommendation")
#     topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

#     if st.sidebar.button("Get Video Recommendations"):
#         video_recommendations = get_video_recommendations(topic_interest, max_results=10)

#         # Display Video Recommendations
#         st.subheader("Video Recommendations")
#         for video in video_recommendations:
#             st.write(f"**{video[0]}**")
#             st.write(f"<img src='{video[6]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
#             st.write(f"Video ID: {video[1]}")
#             st.write(f"Views: {video[2]}")
#             st.write(f"Upload Date: {video[3]}")
#             st.write(f"Channel: {video[4]}")
#             st.write(f"Watch Video: [Link]({video[5]})")
#             st.write("---")

# # Task 3: Sentimental Analysis of Comments with Visualization
# if st.sidebar.checkbox("Sentimental Analysis"):
#     st.sidebar.subheader("Sentimental Analysis")
#     video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

#     # Allow the user to choose the type of comments
#     selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

#     if st.sidebar.button("Analyze Sentiments"):
#         comments_sentiment = get_video_comments(video_id_sentiment)

#         # Filter comments based on the selected sentiment
#         if selected_sentiment == "Positive":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity > 0]
#         elif selected_sentiment == "Neutral":
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity == 0]
#         else:
#             filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity < 0]

#         # Display Advanced Visualization Charts for Comments
#         st.subheader(f"{selected_sentiment.capitalize()} Comments Analysis")

#         # Additional: Word Cloud
#         st.subheader(f"Word Cloud for {selected_sentiment.capitalize()} Comments")
#         wordcloud = generate_word_cloud(filtered_comments)
#         if wordcloud:
#             plt.figure(figsize=(10, 5))
#             plt.imshow(wordcloud, interpolation='bilinear')
#             plt.axis('off')
#             st.pyplot(plt)

#         # Additional: Sentiment Distribution Chart
#         sentiment_df = []
#         for sentiment, sentiment_comments in categorized_comments[selected_sentiment.capitalize()]:
#             sentiment_df.extend([(sentiment, comment[1], comment[2]) for comment in sentiment_comments])

#         sentiment_chart = px.scatter(sentiment_df, x=1, y=2, color=0, labels={'1': 'Polarity', '2': 'Subjectivity'}, title='Sentiment Analysis')
#         st.plotly_chart(sentiment_chart)

#         # Additional: Display Filtered Comments
#         if filtered_comments:
#             st.subheader(f"{selected_sentiment.capitalize()} Comments")
#             for comment in filtered_comments:
#                 st.write(f"- {comment}")
#         else:
#             st.warning(f"No {selected_sentiment.lower()} comments found.")

# # Footer
# st.sidebar.title("Connect with Me")
# st.sidebar.markdown(
#     "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
#     "[GitHub](https://github.com/your-github-profile)"
# )










# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from textblob import TextBlob
import matplotlib.pyplot as plt

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyC1vKniA_REYpyqKYYnpssBffmvbuPT8Ks"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to get channel analytics
def get_channel_analytics(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        channel_info = response.get("items", [])[0]["snippet"]
        statistics_info = response.get("items", [])[0]["statistics"]

        channel_title = channel_info.get("title", "N/A")
        description = channel_info.get("description", "N/A")
        country = channel_info.get("country", "N/A")

        total_videos = int(statistics_info.get("videoCount", 0))
        total_views = int(statistics_info.get("viewCount", 0))

        # Fetch all video details for the dataframe
        videos_df = get_all_video_details(channel_id)

        return channel_title, description, country, total_videos, total_views, videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel analytics: {e}")
        return None, None, None, None, None, None

# Function to fetch all video details for a channel
def get_all_video_details(channel_id):
    try:
        response = youtube.search().list(
            channelId=channel_id,
            type="video",
            part="id,snippet",
            maxResults=50
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            snippet_info = video_info.get("items", [])[0]["snippet"]
            views = int(statistics_info.get("viewCount", 0))
            duration = snippet_info.get("duration", "N/A")
            channel_name = snippet_info.get("channelTitle", "N/A")

            video_details.append((title, video_id, views, duration, channel_name, url))

        videos_df = pd.DataFrame(video_details, columns=["Title", "Video ID", "Views", "Duration", "Channel", "URL"])
        return videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video details: {e}")
        return pd.DataFrame(columns=["Title", "Video ID", "Views", "Duration", "Channel", "URL"])

# Function to get video recommendations based on user's topic
def get_video_recommendations(topic, max_results=10):
    try:
        response = youtube.search().list(
            q=topic,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            order="viewCount"
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            snippet_info = video_info.get("items", [])[0]["snippet"]
            views = int(statistics_info.get("viewCount", 0))
            duration = snippet_info.get("duration", "N/A")
            channel_name = snippet_info.get("channelTitle", "N/A")

            video_details.append((title, video_id, views, duration, channel_name, url))

        return video_details
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video recommendations: {e}")
        return None

# Function to get video comments
def get_video_comments(video_id):
    try:
        comments = []
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        while "items" in results:
            for item in results["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            # Get the next set of results
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    pageToken=results["nextPageToken"],
                    maxResults=100
                ).execute()
            else:
                break

        return comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching comments: {e}")
        return []

# Function to analyze and categorize comments sentiment
def analyze_and_categorize_comments(comments):
    try:
        categorized_comments = {'Positive': [], 'Neutral': [], 'Negative': []}

        for comment in comments:
            analysis = TextBlob(comment)
            # Classify the polarity of the comment
            if analysis.sentiment.polarity > 0:
                categorized_comments['Positive'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
            elif analysis.sentiment.polarity == 0:
                categorized_comments['Neutral'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
            else:
                categorized_comments['Negative'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))

        return categorized_comments
    except Exception as e:
        st.error(f"Error analyzing comments: {e}")
        return {'Positive': [], 'Neutral': [], 'Negative': []}

# Main Streamlit app
st.title("YouTube Analyzer")

# Description of the YouTube Analyzer app
st.markdown(
    """
    Welcome to YouTube Analyzer – your go-to tool for in-depth analysis of YouTube channels and videos! 
    Whether you want to explore detailed analytics for a specific channel, discover top-notch video recommendations, 
    or dive into the sentiment analysis of video comments, this app provides a comprehensive and interactive experience. 
    Gain insights into channel statistics, explore engaging charts, and uncover the sentiment behind the comments. 
    Let's unravel the world of YouTube together!
    """
)

# Sidebar
st.sidebar.title("YouTube Analyzer")
st.sidebar.subheader("Select a Task")

# Task 1: Channel Analytics
if st.sidebar.checkbox("Channel Analytics"):
    st.sidebar.subheader("Channel Analytics")
    channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="YOUR_CHANNEL_ID")

    if st.sidebar.button("Get Channel Analytics"):
        channel_title, description, country, total_videos, total_views, videos_df = get_channel_analytics(channel_id_analytics)

        # Display Channel Overview
        st.subheader("Channel Overview")
        st.write(f"**Channel Title:** {channel_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Country:** {country}")
        st.write(f"**Total Videos:** {total_videos}")
        st.write(f"**Total Views:** {total_views}")

        # Advanced Charts for Channel Analytics
        st.subheader("Advanced Analytics Charts")

        # Time Series Chart for Views
        fig_views = px.line(videos_df, x="Title", y="Views", title="Time Series Chart for Views")
        fig_views.update_layout(height=400, width=800)
        st.plotly_chart(fig_views)

        # Bar Chart for Likes and Comments
        fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
                                    title="Bar Chart for Likes and Comments", barmode="group")
        fig_likes_comments.update_layout(height=400, width=800)
        st.plotly_chart(fig_likes_comments)

        # Additional: Display DataFrame of video details with clickable URLs
        st.subheader("All Video Details")
        videos_df['URL'] = videos_df['URL'].apply(lambda x: f"<a href='{x}' target='_blank'>{x}</a>")
        st.write(videos_df[['Title', 'Video ID', 'Views', 'Duration', 'Channel', 'URL']].to_html(escape=False), unsafe_allow_html=True)

# Task 2: Video Recommendation based on User's Topic of Interest
if st.sidebar.checkbox("Video Recommendation"):
    st.sidebar.subheader("Video Recommendation")
    topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

    if st.sidebar.button("Get Video Recommendations"):
        video_recommendations = get_video_recommendations(topic_interest, max_results=10)

        # Display Video Recommendations
        st.subheader("Video Recommendations")
        for video in video_recommendations:
            st.write(f"**{video[0]}**")
            st.write(f"<img src='{video[4]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
            st.write(f"Video ID: {video[1]}")
            st.write(f"Views: {video[2]}")
            st.write(f"Channel: {video[3]}")
            st.write(f"Watch Video: [Link]({video[5]})")
            st.write("---")

# Task 3: Sentimental Analysis of Comments with Visualization
if st.sidebar.checkbox("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="YOUR_VIDEO_ID")

    # Allow the user to choose the type of comments
    selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

    if st.sidebar.button("Analyze Sentiments"):
        comments_sentiment = get_video_comments(video_id_sentiment)

        # Filter comments based on the selected sentiment
        if selected_sentiment == "Positive":
            filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity > 0]
        elif selected_sentiment == "Neutral":
            filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity == 0]
        else:
            filtered_comments = [comment for comment in comments_sentiment if TextBlob(comment).sentiment.polarity < 0]

        # Display Advanced Visualization Charts for Comments
        st.subheader(f"{selected_sentiment.capitalize()} Comments Analysis")

        # Additional: Sentiment Distribution Chart
        sentiment_df = []
        for sentiment, sentiment_comments in categorized_comments[selected_sentiment.capitalize()]:
            sentiment_df.extend([(sentiment, comment[1], comment[2]) for comment in sentiment_comments])

        sentiment_chart = px.scatter(sentiment_df, x=1, y=2, color=0, labels={'1': 'Polarity', '2': 'Subjectivity'}, title='Sentiment Analysis')
        st.plotly_chart(sentiment_chart)

        # Additional: Display Filtered Comments
        if filtered_comments:
            st.subheader(f"{selected_sentiment.capitalize()} Comments")
            for comment in filtered_comments:
                st.write(f"- {comment}")
        else:
            st.warning(f"No {selected_sentiment.lower()} comments found.")

# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/your-linkedin-profile) | "
    "[GitHub](https://github.com/your-github-profile)"
)
