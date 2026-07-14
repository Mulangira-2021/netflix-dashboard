import subprocess
import sys

# Automatically install plotly if it is missing on the cloud server
try:
    import plotly.express as px
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    import plotly.express as px

import streamlit as st
import pandas as pd

# 1. Page configuration and title layout
st.set_page_config(page_title="Netflix Insights Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("Netflix Titles Dataset Analytics Dashboard")
st.markdown("---")

# 2. Load the pre-cleaned dataset from your notebook pipeline
@st.cache_data
def load_cleaned_data():
    # Reading directly from your pipeline's saved clean CSV
    return pd.read_csv('netflix_titles_cleaned.csv')

try:
    df_clean = load_cleaned_data()
except FileNotFoundError:
    st.error("'netflix_titles_cleaned.csv' not found. Please ensure you run 'df_clean.to_csv(\'netflix_titles_cleaned.csv\', index=False)' at the end of your notebook first.")
    st.stop()

# 3. Interactive Sidebar Controls
st.sidebar.header("Interactive Filtering Panel")

# Filter A: Content Type Selector (Using your engineered dummy columns dynamically)
content_options = ['All Content', 'Movies Only', 'TV Shows Only']
selected_format = st.sidebar.selectbox("Select Content Format:", content_options)

# Filter B: Timeline Range Slider
min_year = int(df_clean['release_year'].min())
max_year = int(df_clean['release_year'].max())
selected_years = st.sidebar.slider("Select Release Year Range:", min_year, max_year, (2010, max_year))

# Filter C: Country Multi-select
available_countries = sorted(df_clean['country'].dropna().unique())
selected_countries = st.sidebar.multiselect("Select Countries (Leave blank for all):", available_countries)

# Apply active filters to the cleaned data vector
df_filtered = df_clean[(df_clean['release_year'] >= selected_years[0]) & (df_clean['release_year'] <= selected_years[1])]

if selected_format == 'Movies Only':
    df_filtered = df_filtered[df_filtered['movie_duration_min'] > 0]
elif selected_format == 'TV Shows Only':
    df_filtered = df_filtered[df_filtered['tv_seasons_count'] > 0]

if selected_countries:
    df_filtered = df_filtered[df_filtered['country'].isin(selected_countries)]

# 4. Key Performance Indicator (KPI) Summary Metrics
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
with metric_col1:
    st.metric("Total Titles Available", f"{len(df_filtered):,}")
with metric_col2:
    total_movies = len(df_filtered[df_filtered['movie_duration_min'] > 0])
    st.metric("Total Movies", f"{total_movies:,}")
with metric_col3:
    total_tv = len(df_filtered[df_filtered['tv_seasons_count'] > 0])
    st.metric("Total TV Shows", f"{total_tv:,}")
with metric_col4:
    st.metric("Max Maturity Rank (Avg)", f"{df_filtered['rating_ordinal'].mean():.1f}")

st.markdown("---")

# 5. Dashboard Grid Visualization Layout
viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    st.subheader("Frequency Distribution of Content Ratings")
    # Filters out any residual missing ratings
    df_ratings = df_filtered[df_filtered['rating_ordinal'] > 0]
    top_ratings = df_ratings['rating'].value_counts().head(10).reset_index()
    top_ratings.columns = ['Rating', 'Count']
    
    fig_bar = px.bar(top_ratings, x='Rating', y='Count', text_auto=True, color='Count', color_continuous_scale='Reds')
    fig_bar.update_layout(xaxis_title="Content Rating", yaxis_title="Total Titles", coloraxis_showscale=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with viz_col2:
    if selected_format != 'TV Shows Only':
        st.subheader("Profile of Movie Durations (Minutes)")
        movies_subset = df_filtered[df_filtered['movie_duration_min'] > 0]
        fig_hist = px.histogram(movies_subset, x='movie_duration_min', nbins=30, color_discrete_sequence=['crimson'], marginal="box")
        fig_hist.update_layout(xaxis_title="Duration (Minutes)", yaxis_title="Frequency Count")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.subheader("Profile of TV Show Seasons")
        tv_subset = df_filtered[df_filtered['tv_seasons_count'] > 0]
        fig_hist = px.histogram(tv_subset, x='tv_seasons_count', color_discrete_sequence=['dodgerblue'], marginal="box")
        fig_hist.update_layout(xaxis_title="Number of Seasons", yaxis_title="Frequency Count")
        st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# 6. Global Footprint Geographic Visualization Map
st.subheader("Production Volume Global Footprint Map")
country_counts = df_filtered['country'].value_counts().reset_index()
country_counts.columns = ['Country', 'Total Titles']
fig_map = px.choropleth(country_counts, locations='Country', locationmode='country names', color='Total Titles', color_continuous_scale='Reds')
fig_map.update_layout(geo=dict(showframe=False, showcoastlines=True), margin=dict(l=0, r=0, t=20, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# 7. Raw Filtered Data Sub-table Explorer (Exhibiting your newly engineered features!)
st.markdown("---")
st.subheader("Preprocessed Data Catalog Explorer Table")
st.dataframe(
    df_filtered[['title', 'director', 'country', 'release_year', 'rating', 'rating_ordinal', 'movie_duration_min', 'tv_seasons_count']], 
    use_container_width=True
)
