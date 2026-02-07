# backend/main.py

import os
import base64
import requests
from math import sqrt
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
    auth = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth.encode()).decode()

    res = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    return res.json()["access_token"]


def search_track(song: str, token: str):
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": song, "type": "track", "limit": 1},
    )
    items = res.json()["tracks"]["items"]
    return items[0] if items else None


def get_audio_features(track_id: str, token: str):
    res = requests.get(
        f"https://api.spotify.com/v1/audio-features/{track_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return res.json()


def get_artist_top_tracks(artist_id: str, token: str):
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": "US"},
    )
    return res.json()["tracks"]


def distance(a, b):
    return sqrt(
        (a["danceability"] - b["danceability"]) ** 2 +
        (a["energy"] - b["energy"]) ** 2 +
        ((a["tempo"] - b["tempo"]) / 200) ** 2 +
        (a["valence"] - b["valence"]) ** 2
    )


@app.get("/recommend")
def recommend(song: str = Query(...)):
    token = get_spotify_token()

    base_track = search_track(song, token)
    if not base_track:
        return {"error": "Song not found"}

    base_features = get_audio_features(base_track["id"], token)

    candidates = get_artist_top_tracks(
        base_track["artists"][0]["id"], token
    )

    best_track = None
    best_score = float("inf")

    for track in candidates:
        if track["id"] == base_track["id"]:
            continue

        features = get_audio_features(track["id"], token)
        score = distance(base_features, features)

        if score < best_score:
            best_score = score
            best_track = track

    return {
        "input_song": base_track["name"],
        "recommended_song": best_track["name"],
        "artist": best_track["artists"][0]["name"],
        "spotify_url": best_track["external_urls"]["spotify"],
        "similarity_score": round(best_score, 4),
    }
