from spotify_local import SpotifyLocal
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import check_app as ca
import os
from dotenv import load_dotenv

load_dotenv()


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Define permissions (scopes) to control playback
scope = "user-modify-playback-state user-read-playback-state"

# Log into the cloud API
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
))


def search_and_play(song_name):
    ca.smart_launch("spotify")
    print(f"Searching Spotify's cloud for: '{song_name}'...")

    # 1. Put your song name string into the search function
    results = sp.search(q=song_name, limit=1, type='track')

    # Check if a track was actually found
    if not results['tracks']['items']:
        print("No tracks found with that name.")
        return

    # 2. Extract the cloud track information and URI
    track = results['tracks']['items'][0]
    track_uri = track['uri']
    track_name = track['name']
    artist_name = track['artists'][0]['name']

    print(f"Found: {track_name} by {artist_name}")
    print(f"Track Cloud URI: {track_uri}")

    try:
        # 3. Tell your active Spotify player to play this specific track URI
        print("Sending play command to your device...")
        sp.start_playback(uris=[track_uri])
        print("Success! Enjoy your music.")
    except Exception as e:
        print(f"\n[Error] Could not start playback: {e}")
        print(
            "Fix: Open the Spotify App on your phone or PC, hit play on any song manually to make the device 'active', then run this script again!")