import streamlit as st
from pymongo import MongoClient
import requests
import re
import bcrypt
import os

# Initialize MongoDB client
client = MongoClient('mongodb://localhost:27017/')
db = client['music']
users_collection = db['users']
liked_songs_collection = db['liked_songs']
playlists_collection = db['playlist']
search_history_collection = db['search_history']
downloaded_songs_collection = db['downloaded_songs']  # New collection for downloaded songs

# Spotify API setup
API_ENDPOINT = 'https://v1.nocodeapi.com/vigneshgoud/spotify/slmMZitLKMHvByQx'
API_KEY = os.getenv('SPOTIFY_API_KEY', 'slmMZitLKMHvByQx')

# Function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Function to check passwords
def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

# Sign-up function
def sign_up(username, password):
    if not re.search(r'[A-Za-z]', password):
        st.error("Password must contain at least one letter.")
        return
    if not re.search(r'[0-9]', password):
        st.error("Password must contain at least one number.")
        return
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        st.error("Password must contain at least one symbol.")
        return
    if username == password:
        st.error("Username and password should not be the same.")
        return

    hashed_password = hash_password(password)
    user = {"username": username, "password": hashed_password}
    users_collection.insert_one(user)
    st.success("You have successfully signed up!")

# Login function
def login(username, password):
    user = users_collection.find_one({"username": username})

    if user:
        if check_password(user['password'], password):
            st.session_state.user_logged_in = True
            st.session_state.username = username
            st.success("Logged in successfully!")
            return True
        else:
            st.error("Invalid username or password")
            return False
    else:
        st.error("No username found. Please create a new account.")
        return False

# Function to make API requests
def api_request(endpoint, params=None, method='GET'):
    url = f"{API_ENDPOINT}/{endpoint}"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request(method, url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        st.error(f"Request error occurred: {req_err}")
    except Exception as err:
        st.error(f"Other error occurred: {err}")
    return {}

# Function to add song to liked songs
def add_to_liked_songs(track):
    liked_song = {"username": st.session_state.username, "track": track}
    liked_songs_collection.insert_one(liked_song)
    st.success("Song added to liked songs!")

# Function to add song to playlist
def add_to_playlist(track):
    playlist_name = st.text_input("Enter playlist name", key='playlist_input')
    button_key = f"add_to_playlist_{track['id']}"

    if st.button("Add to Playlist", key=button_key):
        if playlist_name:
            playlist = playlists_collection.find_one({"username": st.session_state.username, "playlist_name": playlist_name})
            if playlist:
                if any(t['id'] == track['id'] for t in playlist.get('tracks', [])):
                    st.warning("This song is already in the playlist.")
                else:
                    playlists_collection.update_one({"_id": playlist["_id"]}, {"$push": {"tracks": track}})
                    st.success("Song was added to your playlist!")
            else:
                st.error("Playlist not found. Please create the playlist first.")
        else:
            st.error("Please enter a playlist name.")

# Function to save search history
def save_search_history(query):
    search_record = {"username": st.session_state.username, "query": query}
    search_history_collection.insert_one(search_record)

# Function to download a song
def download_song(track):
    downloaded_song = {"username": st.session_state.username, "track": track}
    downloaded_songs_collection.insert_one(downloaded_song)
    st.success("Song downloaded!")

# Function to display downloaded songs
def display_downloaded_songs():
    st.write("Downloaded Songs")
    downloaded_songs = downloaded_songs_collection.find({"username": st.session_state.username})
    for song in downloaded_songs:
        track = song['track']
        track_uri = track.get('uri')
        st.markdown(f"""
        <iframe src="https://open.spotify.com/embed/track/{track_uri.split(':')[-1]}" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
        """, unsafe_allow_html=True)

# Streamlit app layout
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False

# Login/Signup Page with styling
if not st.session_state.user_logged_in:
    st.markdown("""
    <style>
    body {
        background-color: #1DB954;  /* Spotify green */
        color: white;
        font-family: 'Arial', sans-serif;
    }
    .title {
        text-align: center;
        font-size: 40px;
        margin-bottom: 20px;
    }
    .input {
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Login and Sign-up Page")

    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username", key='signup_username', placeholder="Enter Username")
        new_password = st.text_input("Password", type='password', placeholder="Enter Password")
        if st.button("Sign Up"):
            sign_up(new_user, new_password)

    elif choice == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username", placeholder="Enter Username")
        password = st.text_input("Password", type='password', placeholder="Enter Password")
        if st.button("Login"):
            if login(username, password):
                st.session_state.user_logged_in = True
                st.session_state.current_track = None
                st.session_state.playing_track_uri = None
                st.rerun()

# MY_MUSIC Dashboard with styling
if st.session_state.user_logged_in:
    st.markdown("""
    <style>
    body {
        background-color: #282828;  /* Dark background */
        color: #ffffff;
        font-family: 'Arial', sans-serif;
    }
    h1 {
        color: #1DB954;  /* Spotify green */
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("MY_MUSIC")
    st.markdown(f"**_Welcome, {st.session_state.username}_**")

    # Sidebar menu buttons
    st.sidebar.title("Menu")

    if st.sidebar.button("Search"):
        st.session_state.active_section = "search"
    if st.sidebar.button("My Playlists"):
        st.session_state.active_section = "playlists"
    if st.sidebar.button("Liked Songs"):
        st.session_state.active_section = "liked_songs"
    if st.sidebar.button("Downloaded Songs"):
        st.session_state.active_section = "downloaded_songs"

    if st.sidebar.button("Logout"):
        st.session_state.user_logged_in = False
        st.session_state.username = None
        st.success("You have successfully logged out.")
        st.rerun()

    if 'active_section' not in st.session_state:
        st.session_state.active_section = "search"

    if st.session_state.playing_track_uri:
        st.markdown(f"""
        <iframe src="https://open.spotify.com/embed/track/{st.session_state.playing_track_uri.split(':')[-1]}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
        """, unsafe_allow_html=True)

    if st.session_state.active_section == "search":
        search_query = st.text_input("Search for a song or artist")

        if search_query:
            save_search_history(search_query)
            search_results = api_request('search', params={'q': search_query, 'type': 'track', 'limit': 10})

            if search_results:
                tracks = search_results.get('tracks', {}).get('items', [])

                if tracks:
                    track_names = [track['name'] for track in tracks]
                    selected_track = st.selectbox("Choose a song", track_names)

                    selected_track_details = next(track for track in tracks if track['name'] == selected_track)
                    track_uri = selected_track_details.get('uri')
                    track = selected_track_details

                    st.session_state.playing_track_uri = track_uri
                    st.markdown(f"""
                    <iframe src="https://open.spotify.com/embed/track/{track_uri.split(':')[-1]}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
                    """, unsafe_allow_html=True)

                    if st.button("Like"):
                        add_to_liked_songs(track)
                    if st.button("Add to Playlist"):
                        add_to_playlist(track)
                    if st.button("Download"):
                        download_song(track)  # Download the song and save it in the database
                else:
                    st.write("No songs found.")
            else:
                st.write("No results from API.")

    elif st.session_state.active_section == "playlists":
        st.write("My Playlists")
        playlists = playlists_collection.find({"username": st.session_state.username})
        for playlist in playlists:
            st.write(f"**{playlist['playlist_name']}**")
            for track in playlist.get('tracks', []):
                track_uri = track.get('uri')
                st.markdown(f"""
                <iframe src="https://open.spotify.com/embed/track/{track_uri.split(':')[-1]}" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
                """, unsafe_allow_html=True)

    elif st.session_state.active_section == "liked_songs":
        st.write("Liked Songs")
        liked_songs = liked_songs_collection.find({"username": st.session_state.username})
        for song in liked_songs:
            track = song['track']
            track_uri = track.get('uri')
            st.markdown(f"""
            <iframe src="https://open.spotify.com/embed/track/{track_uri.split(':')[-1]}" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
            """, unsafe_allow_html=True)

    elif st.session_state.active_section == "downloaded_songs":
        display_downloaded_songs()  # Display downloaded songs
