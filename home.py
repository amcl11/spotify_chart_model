# Dependencies 
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import plotly.express as px
from sqlalchemy import create_engine, text
import os

from PIL import Image
import requests
from io import BytesIO


# Set right aligned note about Desktop viewing 
col1, col2, col3 = st.columns([6, 6, 6])

with col3:
    st.write(
        """
        <style>
            .my-text {
                font-size: 10px;
                font-family: monospace;
            }
        </style>
        <p class="my-text">[Best viewed on Desktop]</p>
        """,
        unsafe_allow_html=True,
    )
    
# Setup DATABASE_URL and engine
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)


##################################
# TITLE INFO
##################################
st.title('New Release Playlist Adds:')
left_column, middle_column, right_column = st.columns(3)
# left_column.image('images/nmf_logo_transparent_background.png')

st.write('This site streamlines Friday morning playlist checking for those interested in New Release coverage on Spotify in Australia.')
st.markdown("All songs added to <span style='color: white;'>*New Music Friday AU & NZ*</span> are fetched, and then checked against key editorial playlists.", unsafe_allow_html=True)
st.write("For more info and the list of playlists that are tracked, check the *about* page.")  
st.markdown("""
    <style>
    .small-font {
        font-size: 14px;
    }
    </style>
    
    <p class="small-font">Note: This means New Releases that did not get added to NMF AU & NZ will not show up on this site - focusing on the releases that Spotify has chosen to feature in NMF.</p>
    """, unsafe_allow_html=True)

st.write('---')  # Add a visual separator

##################################
# DISPLAY MOST RECENT FRIDAY DATE
##################################

# Get the current datetime
now = datetime.now()
# Determine the current day of the week (0=Monday, 6=Sunday)
weekday = now.weekday()

# Calculate the days to subtract to get the most recent Friday
days_to_subtract = (weekday - 4) % 7
most_recent_friday = now - timedelta(days=days_to_subtract)

# Create a custom function to format the day with the suffix
def add_suffix_to_day(day):
    return f"{day}{('th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th'))}"

# Format the most recent Friday date
day_with_suffix = add_suffix_to_day(most_recent_friday.day)
most_recent_friday_str = most_recent_friday.strftime(f"Release Date: {day_with_suffix} %B, %Y")

# Display the most recent Friday 
st.subheader(most_recent_friday_str)

############################################################################################
# MAIN FUNCTION TO LOAD LATEST FRIDAY DATA FOR HOME.PY - Cached for 58.33 mins (ttl=3500) 
############################################################################################

@st.cache_data(ttl=350, show_spinner='Fetching New Releases...')
def load_db_for_most_recent_date():
    query = text("""
    SELECT * FROM nmf_spotify_coverage
    WHERE "Date" = (SELECT MAX("Date") FROM nmf_spotify_coverage)
    """)
    with engine.connect() as connection:
        result = connection.execute(query)
        # Ensure columns are correctly extracted from result
        columns = result.keys()  # list of column names
        latest_friday_df = pd.DataFrame(result.fetchall(), columns=columns)
    return latest_friday_df

# Main dataframe to use for home.py 
latest_friday_df = load_db_for_most_recent_date()

# Set columns for metrics 
col1, col2 = st.columns([50, 50])  

# Set metric text size
st.markdown(
    """
<style>
[data-testid="stMetricValue"] {
    font-size: 18px;
}
</style>
""",
    unsafe_allow_html=True,
)
# Remove download and other buttons from all Dataframes
st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

# Filter the DataFrame to get rows matching the NMF playlist
filtered_df = latest_friday_df[latest_friday_df['Playlist'] == "New Music Friday AU & NZ"]

# Function to load image from URL
def load_image_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return image
        else:
            return None
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

# Filter the DataFrame to get rows matching the NMF playlist
filtered_df = latest_friday_df[latest_friday_df['Playlist'] == "New Music Friday AU & NZ"]

# Ensure the filtered DataFrame is not empty and the Image_URL is not null before extracting the Image URL
if not filtered_df.empty and pd.notna(filtered_df['Image_URL'].iloc[0]):
    image_url = filtered_df['Image_URL'].iloc[0]
    cover_artist = filtered_df['Cover_Artist'].iloc[0] if 'Cover_Artist' in filtered_df.columns and pd.notna(filtered_df['Cover_Artist'].iloc[0]) else None

    if image_url:  # Check if the URL is not empty
        todays_cover_image = load_image_from_url(image_url)
        if todays_cover_image:
            if cover_artist:
                col2.image(image_url, caption=f"Cover Artist: {cover_artist}", width=300)
            else:
                col2.image(image_url, width=300)
                col2.write("Cover Artist not available.")
        else:
            col2.write("Failed to load image from URL.")
    else:
        col2.write("No cover image available this week.")
else:
    col2.write("Current NMF image not available.")


# # Function to load image from URL
# def load_image_from_url(url):
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             image = Image.open(BytesIO(response.content))
#             return image
#         else:
#             return None
#     except Exception as e:
#         print(f"Error loading image: {e}")
#         return None

# # Ensure the filtered DataFrame is not empty and the Image_URL is not null before extracting the Image URL
# if not filtered_df.empty and pd.notna(filtered_df['Image_URL'].iloc[0]):
#     image_url = filtered_df['Image_URL'].iloc[0]
#     if image_url:  # Check if the URL is not empty
#         todays_cover_image = load_image_from_url(image_url)
#         if todays_cover_image:
#             col2.image(todays_cover_image)
#         else:
#             col2.image("Failed to load image from URL.")
#     else:
#         col2.write("No cover image available this week.")
# else:
#     col2.write("Current NMF image not available.")



#######################
# HIGHEST REACH METRIC 
#######################

# Assuming latest_friday_df is your DataFrame
# Group by 'Title' and 'Artist', then sum the 'Followers' column
highest_reach = latest_friday_df.groupby(['Title', 'Artist'])['Followers'].sum().reset_index(name='Reach')

# Find the maximum reach
max_reach = highest_reach['Reach'].max()

# Filter to get the titles with the maximum reach
highest_reach_max = highest_reach[highest_reach['Reach'] == max_reach].reset_index(drop=True)

# Collect all artist-title pairs into a list (without including the reach value)
artist_title_pairs = [f"{row['Artist']} - '{row['Title']}'" for _, row in highest_reach_max.iterrows()]

# Sort the list alphabetically
artist_title_pairs.sort()

# Prepare the HTML string without bullet points, using line breaks to separate items
artist_title_html = "<div style='margin-top: -10px;'>" + "<br>".join(artist_title_pairs) + "</div>"

# Display the metric with the label and the delta (total reach)
with col1:
    st.metric(label=":grey[Highest Reach]", value="", delta=f"{round(max_reach):,}", help='Total reach across AU playlist adds. Only based on the tracked playlists.')

# Use markdown to display the artist-title pairs underneath the metric
    st.markdown(artist_title_html, unsafe_allow_html=True)
    st.write("")
    st.write("")


#######################
# MOST ADDED METRIC
#######################

# Assuming latest_friday_df is your DataFrame
# Find the titles with the most entries
most_added = latest_friday_df.groupby(['Title', 'Artist']).size().reset_index(name='Count')
max_count = most_added['Count'].max()
most_added_max = most_added[most_added['Count'] == max_count].reset_index(drop=True)

# Collect all artist-title pairs into a list
artist_title_pairs = [f"{row['Artist']} - '{row['Title']}'" for _, row in most_added_max.iterrows()]

# Sort the list alphabetically
artist_title_pairs.sort()

# Prepare the HTML string without bullet points, using line breaks to separate items
artist_title_html = "<div style='margin-top: -10px;'>" + "<br>".join(artist_title_pairs) + "</div>"

# Display the metric with the label and the delta
with col1:
    st.metric(label=":grey[Most Added]", value="", delta=f"Added to {max_count} playlists")

# Use markdown to display the artist-title pairs underneath the metric
    st.markdown(artist_title_html, unsafe_allow_html=True)
    st.write("")
    st.write("")


####################################
# HIGHEST AVERAGE PLAYLIST POSITION 
####################################

# Use latest_friday_df from earlier in the code
# Group by 'Title' and 'Artist', then find the average 'Position'
avg_position = latest_friday_df.groupby(['Title', 'Artist'])['Position'].mean().reset_index(name='AvgPosition')

# Find the minimum average position
min_avg_position = avg_position['AvgPosition'].min()

# Filter to get the titles and artists with the minimum average position
lowest_avg_position = avg_position[avg_position['AvgPosition'] == min_avg_position].reset_index(drop=True)

# Collect all artist-title pairs into a list
artist_title_pairs = [f"{row['Artist']} - '{row['Title']}'" for _, row in lowest_avg_position.iterrows()]

# Sort the list alphabetically
artist_title_pairs.sort()

# Prepare the HTML string without bullet points, using line breaks to separate items
artist_title_html = "<div style='margin-top: -10px;'>" + "<br>".join(artist_title_pairs) + "</div>"

# Display the metric with the label and the empty value, then the HTML list
with col1:
    # Display the metric with an empty value but with help text
    st.metric(label=":grey[Highest Average Playlist Position]", value="", delta=f"Average Position: {min_avg_position:.1f}", help='Averages all positions across any new AU playlist additions.')
    
    # Use markdown to display the artist-title pairs underneath the metric
    st.markdown(artist_title_html, unsafe_allow_html=True)
    st.write("") 
    st.write("") 

 
st.write("----")


########################################################## 
# TOP 5 HIGHEST REACH CHART
########################################################## 

st.write(
    """
    <style>
        .my-text {
            font-size: 12px;
            font-family: monospace;
        }
    </style>
    <p class="my-text">Hover over chart to check playlist details</p>
    """,
    unsafe_allow_html=True,
)

# Use latest_friday_df from earlier in the code
top_artists_reach = latest_friday_df.groupby(['Artist', 'Title']).agg({
    'Followers': 'sum',
    'Playlist': lambda x: list(x.unique())  # Creates a list of unique playlists for each artist
})

# Sort the DataFrame based on 'Followers' while maintaining the whole DataFrame
sorted_top_artists_reach = top_artists_reach.sort_values(by='Followers', ascending=False)

# Select the top 5 artists while keeping all columns ('Followers' and 'Playlist')
results_with_playlist = sorted_top_artists_reach.head(5).copy()

# Join the playlist names with '<br>' to create a single string with line breaks
results_with_playlist['Playlists_str'] = results_with_playlist['Playlist'].apply(lambda x: '<br>'.join(x))

# Ensure 'Artist' is a column for Plotly (if 'Artist' was the index)
results_with_playlist = results_with_playlist.reset_index()

# Combine 'Artist' and 'Title' into a unique identifier
results_with_playlist['Artist_Title'] = results_with_playlist['Artist'] + ' - ' + results_with_playlist['Title']


# Calculate maximum value of 'total_followers' and add a larger buffer
max_value = results_with_playlist['Followers'].max()
buffer = max_value * 0.2  # adjust this buffer percentage as needed

# Create a color scale
color_scale = [[0, 'lightsalmon'], [0.5, 'coral'], [1, 'orangered']]

# Create a bar chart using Plotly Express
fig = px.bar(results_with_playlist, x='Artist_Title', y='Followers',
             text='Followers',
             hover_data=['Title', 'Playlists_str'],  # Add 'Playlist_str' to hover data
             color='Followers',  # Assign color based on 'Followers' values
             color_continuous_scale=color_scale  # Use custom color scale
             )

# Custom hover template
fig.update_traces(hovertemplate='<b>%{x}</b> <br>%{customdata[1]}',
                  textposition='outside',
                  texttemplate='%{text:.3s}'
                  )

# Layout adjustments
fig.update_layout(
    yaxis=dict(
        title='Total Playlist Reach',
        range=[0, max_value + buffer],  # Extend the range beyond the highest bar
        automargin=True,  # Let Plotly adjust the margin automatically
    ),
    xaxis=dict(
        tickangle=20,
        title = '',
        automargin=True,  # Let Plotly adjust the margin automatically
    ),
    plot_bgcolor='rgba(0,0,0,0)',  # Set background color to transparent
    paper_bgcolor='#0E1117',  # Set the overall figure background color
    margin=dict(t=80, l=40, r=40, b=40),  # Adjust margin to make sure title fits
    title=dict(
        text='Top 5 Highest Reach',
        font=dict(family="Arial, sans-serif", size=18, color="white"),
        y=0.9,  # Position title within the top margin of the plotting area
        x=0.5,  # Center the title on the x-axis
        xanchor='center',
        yanchor='top'
    ),
    showlegend=False,
    coloraxis_showscale=False
)


# Display the figure in Streamlit
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


########################
# SEARCH ADDS BY SONG
########################

st.subheader('Search Adds By Song:')

# Combine Artist & Title for the first dropdown box: 
# Use latest_friday_df from earlier in the code

# Filter out rows where either 'Artist' or 'Title' is null for dropdown creation
filtered_df_for_artist_title = latest_friday_df.dropna(subset=['Artist', 'Title'])

# Temporarily create 'Artist_Title' in the filtered dataframe for dropdown options
filtered_df_for_artist_title['Artist_Title'] = filtered_df_for_artist_title['Artist'] + " - " + filtered_df_for_artist_title['Title']

# Ensure unique values and sort them for the dropdown
choices = filtered_df_for_artist_title['Artist_Title'].unique()
sorted_choices = sorted(choices, key=lambda x: x.lower())

# Dropdown for user to select an artist and title
selected_artist_title = st.selectbox('Select New Release:', sorted_choices)

# Add 'Artist_Title' to the original dataframe for filtering based on the dropdown selection
latest_friday_df['Artist_Title'] = latest_friday_df.apply(lambda row: f"{row['Artist']} - {row['Title']}" if pd.notnull(row['Artist']) and pd.notnull(row['Title']) else None, axis=1)

# Now filter the original DataFrame based on selection, this time it includes 'Artist_Title'
filtered_df = latest_friday_df[latest_friday_df['Artist_Title'] == selected_artist_title].drop(columns=['Artist', 'Title', 'Artist_Title'])

# Ensure 'Followers' is numeric for proper sorting
filtered_df['Followers'] = pd.to_numeric(filtered_df['Followers'], errors='coerce')

# Continue with sorting and displaying the data 
ordered_filtered_df = filtered_df.sort_values(by='Followers', ascending=False)

#### By removing this line, ordered_filtered_df['Followers'] remains in a numeric format, which should allow Streamlit to handle sorting properly when you click on the column headers in the displayed DataFrame.
# # Before displaying, round 'Followers' to no decimal places and format
# ordered_filtered_df['Followers'] = ordered_filtered_df['Followers'].apply(lambda x: f"{round(x):,}" if pd.notnull(x) else "N/A")

# Display the table with only the 'Playlist', 'Position', and 'Followers' columns, ordered by 'Followers'
st.dataframe(ordered_filtered_df[['Playlist', 'Position', 'Followers']], use_container_width=False, hide_index=True)


###########################
# SEARCH ADDS BY PLAYLIST
###########################

st.write("")
st.subheader('Search Adds By Playlist:')

# Use latest_friday_df from earlier in the code
playlist_choices = sorted(latest_friday_df['Playlist'].unique(), key=lambda x: x.lower())

selected_playlist = st.selectbox('Select Playlist:', playlist_choices, key='playlist_select')

# Filter DataFrame based on the selected playlist
filtered_playlist_df = latest_friday_df[latest_friday_df['Playlist'] == selected_playlist]

# Check if 'Artist' and 'Title' columns only contain None values
if filtered_playlist_df[['Artist', 'Title']].isnull().all(axis=None):
    st.markdown(f"<span style='color: #FAFAFA;'>No New Releases added to <span style='color: salmon;'>**{selected_playlist}**</span> that were also added to NMF AU & NZ</span>", unsafe_allow_html=True)

else:
    sorted_df = filtered_playlist_df.sort_values(by='Position', ascending=True)
    # Clean the DataFrame to replace None with 'N/A' for display
    sorted_df[['Artist', 'Title', 'Position']] = sorted_df[['Artist', 'Title', 'Position']].fillna('N/A')
    st.data_editor(
        data=sorted_df[['Artist', 'Title', 'Position']],
        disabled=True,  # Ensures data cannot be edited
        use_container_width=False,  
        column_config={
            "Artist": {"width": 150},  # Set tighter width
            "Title": {"width": 120},   # Set width
            "Position": {"width": 58}
        },
        hide_index=True
    )

#################################################
# Cover Artists DataFrame 
#################################################

# Filter out rows where either 'Cover_Artist' or 'Image_URL' is None before grouping
# Use latest_friday_df from earlier in the code
filtered_df = latest_friday_df.dropna(subset=['Cover_Artist', 'Image_URL'])

new_cover_artist_df = filtered_df.groupby('Playlist').agg({
    'Image_URL': 'first',
    'Cover_Artist': 'first'
}).reset_index()

final_cover_artist_df = new_cover_artist_df[['Playlist', 'Cover_Artist']]

# renamed column for display
display_df = final_cover_artist_df.rename(columns={'Cover_Artist': 'Cover Artist'})

st.subheader('Cover Artists:')
st.dataframe(display_df, use_container_width=False, hide_index=True)

st.write("") # padding 
st.write("*Cover artist may update before cover images*")

#################################################################################
# New Playlist packshots code - to centre the final image if the number is odd. 
#################################################################################

# Determine if there is an odd number of playlists
total_playlists = len(new_cover_artist_df)
is_odd = total_playlists % 2 != 0

# If the number of playlists is odd, then we reserve the last spot for the single centered image
if is_odd:
    last_image_col_index = total_playlists - 1  # Index of the last image
else:
    last_image_col_index = None  # No special handling needed if even

# Create two columns for the images
col1, col2 = st.columns(2)

# Initialize an index for the last column, will be used if there's an odd number of images
last_col = None

# Iterate over DataFrame rows
for index, row in new_cover_artist_df.iterrows():
    playlist_name = row['Playlist']
    artist_name = row['Cover_Artist']
    image_url = row['Image_URL']
    
    # Check if we're at the last image and if it should be centered
    if index == last_image_col_index:
        # Create a new set of columns for the last image
        _, last_col, _ = st.columns([1, 2, 1])  # Middle column is twice as wide to center the image
        last_col.image(image_url, caption=f"Cover Artist: {artist_name}", width=300)
    else:
        # Use the two columns as before
        col_index = index % 2
        col = col1 if col_index == 0 else col2
        col.image(image_url, caption=f"Cover Artist: {artist_name}", width=300)

st.write('- - - - - -') 

################################
# ADDS BY PLAYLIST GRAPH
################################

# # Calculate the number of adds per playlist and sort for plotting
# # Use latest_friday_df from earlier in the code

# Filter out rows with both null 'Artist' and 'Title'
non_null_adds_df = latest_friday_df.dropna(subset=['Artist', 'Title'])

# Count the number of adds per playlist only for non-null 'Artist' and 'Title'
adds_per_playlist = non_null_adds_df['Playlist'].value_counts().reindex(latest_friday_df['Playlist'].unique(), fill_value=0).sort_values()

fig, ax = plt.subplots(figsize=(6, 8), facecolor= '#0E1117')
adds_per_playlist.plot(kind='barh', ax=ax, color='#ab47bc')

ax.set_facecolor('#0E1117')
fig.patch.set_facecolor('#0E1117')

# Customise tick parameters 
ax.tick_params(axis='x', colors='white', labelsize=12, bottom=False, labelbottom=False)  # Hide x ticks
ax.tick_params(axis='y', colors='white', labelsize=12)
ax.tick_params(axis='y', which='both', left=False, labelleft=True)  # Remove Y-axis ticks but keep labels

# Reduced padding between title and x-axis label
ax.set_title('Adds By Playlist', pad=15, weight='bold', color='white', fontsize=20, loc='left')

ax.grid(False)
ax.xaxis.set_label_position('top')

# Custom formatting for x-axis label with reduced label padding
ax.set_xlabel('No. of New Releases Added', labelpad=10, weight='light', color='white', fontsize=10, loc='left')

# Add text labels at the end of each bar
for index, value in enumerate(adds_per_playlist):
    ax.text(value + 1, index, str(value), color='white', va='center', ha='left')

# Remove spines
for location in ['left', 'right', 'top', 'bottom']:
    ax.spines[location].set_visible(False)

st.pyplot(fig)
