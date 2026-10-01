import streamlit as st
import pandas as pd
import plotly.express as px
from textblob import TextBlob

st.set_page_config(
    page_title="TAlker Analysis",
    page_icon="🦙",
    layout="wide",
)

posts_df = pd.read_csv('../data/posts.csv')

def make_plot_1(posts_df):
    posts_df['date'] = pd.to_datetime(posts_df['timestamp'])  # Assuming 'created' is a column with timestamps
    posts_over_time = posts_df.resample('W', on='date').size()  # Weekly aggregation
    fig = px.line(posts_over_time, title='Posts Over Time', color_discrete_sequence=['indianred'])
    st.plotly_chart(fig)

def make_plot_2(posts_df):
    user_posts_counts = posts_df['username'].value_counts()  # Assuming 'username' denotes the post author
    fig = px.histogram(x=user_posts_counts.values, nbins=20, title='User Participation', color_discrete_sequence=['indianred'])
    st.plotly_chart(fig)

def make_plot_3(posts_df):
    posts_df['post_length'] = posts_df['content'].apply(len)
    fig = px.histogram(posts_df, x='post_length', title='Distribution of Post Lengths',
                    labels={'post_length': 'Post Length (characters)'},
                    nbins=50,  # Adjust the number of bins for better granularity
                    color_discrete_sequence=['indianred'])  # Color can be adjusted
    st.plotly_chart(fig)

def make_plot_4(posts_df):
    posts_df['sentiment'] = posts_df['content'].apply(lambda x: TextBlob(x).sentiment.polarity)
    fig = px.histogram(posts_df, x='sentiment', nbins=20, title='Sentiment Distribution of Posts', color_discrete_sequence=['indianred'])
    st.plotly_chart(fig)

st.title("Analysis")
col1, col2 = st.columns(2)
with col1:
    make_plot_1(posts_df)
    make_plot_2(posts_df)
with col2:
    make_plot_3(posts_df)
    make_plot_4(posts_df)

    