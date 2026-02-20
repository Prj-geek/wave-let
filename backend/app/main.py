# backend/main.py

import os
import base64
import time
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

# -------- TOKEN CACHE --------
spotify_token = None
token_expires_at = 0


def get_spotify_token():
    global spotify_token, token_expires_at

    if spotify_token and time.time() < token_expires_at:
        return spotify_token

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

    data = res.json()
    spotify_token = data["access_token"]
    token_expires_at = time.time() + data["expires_in"] - 60

    return spotify_token


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

def generate_explanation(base, candidate):
    differences = {
        "danceability": abs(base["danceability"] - candidate["danceability"]),
        "energy": abs(base["energy"] - candidate["energy"]),
        "tempo": abs(base["tempo"] - candidate["tempo"]),
        "valence": abs(base["valence"] - candidate["valence"]),
    }

    # Find most similar feature (smallest difference)
    most_similar = min(differences, key=differences.get)

    explanations = {
        "danceability": "It has a very similar danceability level.",
        "energy": "It matches the energy of your song.",
        "tempo": "It has a similar tempo and pacing.",
        "valence": "It carries a similar emotional tone.",
    }

    return explanations[most_similar]


def get_audio_features_batch(track_ids: list, token: str):
    ids_string = ",".join(track_ids[:100])  # Spotify limit = 100
    res = requests.get(
        "https://api.spotify.com/v1/audio-features",
        headers={"Authorization": f"Bearer {token}"},
        params={"ids": ids_string},
    )
    return res.json().get("audio_features", [])


@app.get("/recommend")
def recommend(song: str = Query(...)):
    token = get_spotify_token()

    base_track = search_track(song, token)
    if not base_track:
        return {"error": "Song not found"}

    base_features = get_audio_features(base_track["id"], token)

    artist_id = base_track["artists"][0]["id"]
    artist_data = get_artist(artist_id, token)

    candidates = []

    # Same artist
    candidates.extend(get_artist_top_tracks(artist_id, token))

    # Same genre
    genres = artist_data.get("genres", [])
    for genre in genres[:2]:
        candidates.extend(search_by_genre(genre, token))

    scored_tracks = []
    seen_ids = set()

    for track in candidates:
        if track["id"] == base_track["id"]:
            continue
        if track["id"] in seen_ids:
            continue

        seen_ids.add(track["id"])

        features = get_audio_features(track["id"], token)
        if not features:
            continue

        score = distance(base_features, features)

        scored_tracks.append({
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "spotify_url": track["external_urls"]["spotify"],
            "similarity_score": score,
            "why": generate_explanation(base_features, features)
        })
        

    # Sort by similarity (lowest first)
    scored_tracks.sort(key=lambda x: x["similarity_score"])

    top_recommendations = scored_tracks[:5]

   result = {
    "input_song": base_track["name"],
    "recommendations": [
        {
            "name": t["name"],
            "artist": t["artist"],
            "spotify_url": t["spotify_url"],
            "similarity_score": round(t["similarity_score"], 4),
            "why": t["why"]
        }
        for t in top_recommendations
    ]
}

recommendation_cache[cache_key] = {
    "data": result,
    "expires_at": time.time() + CACHE_TTL
}

return result

