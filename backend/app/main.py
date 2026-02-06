# backend/main.py

import os
import base64
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

app = FastAPI(title="Wave-let API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_spotify_token():
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )

    return response.json()["access_token"]


def search_track(song_name: str, token: str):
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": song_name,
            "type": "track",
            "limit": 1,
        },
    )

    items = response.json()["tracks"]["items"]
    return items[0] if items else None


def get_audio_features(track_id: str, token: str):
    response = requests.get(
        f"https://api.spotify.com/v1/audio-features/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()


@app.get("/")
def root():
    return {"status": "Wave-let backend running"}


@app.get("/recommend")
def recommend(song: str = Query(...)):
    token = get_spotify_token()

    track = search_track(song, token)
    if not track:
        return {"error": "Song not found"}

    audio_features = get_audio_features(track["id"], token)

    return {
        "input_song": song,
        "track": {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "spotify_url": track["external_urls"]["spotify"],
        },
        "audio_features": {
            "danceability": audio_features["danceability"],
            "energy": audio_features["energy"],
            "tempo": audio_features["tempo"],
            "valence": audio_features["valence"],
        },
    }
