import requests
from urllib.parse import urlencode
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

CLIENT_ID = "8969f7ba5dde4581ba4121d123298775"
CLIENT_SECRET = "0ec67d1c9258433fa270183248207d91"
REDIRECT_URI = "http://127.0.0.1:8000/callback"
SCOPES = "user-read-private user-read-email streaming user-library-read"

# Store access tokens (use database in production)
user_tokens = {}


@app.get("/")
def root():
    return {"message": "Wavelet API is running"}


@app.get("/login")
def login():
    """Redirect user to Spotify login"""
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "show_dialog": "true"
    }
    
    full_url = f"{auth_url}?{urlencode(params)}"
    return RedirectResponse(url=full_url)


@app.get("/test-search")
def test_search():
    """Test if search endpoint works"""
    token = user_tokens.get("current_user")
    
    if not token:
        return {"error": "Not authenticated. Visit /login first"}
    
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": "Shape of You", "type": "track", "limit": 1}
    
    response = requests.get(url, headers=headers, params=params)
    print(f"Search status: {response.status_code}")
    
    if response.status_code == 200:
        return {"status": "Search works!", "data": response.json()}
    else:
        return {"status": f"Search failed: {response.status_code}", "data": response.text}


@app.get("/test-audio/{track_id}")
def test_audio_direct(track_id: str):
    """Test audio-features endpoint directly"""
    token = user_tokens.get("current_user")
    
    if not token:
        return {"error": "Not authenticated. Visit /login first"}
    
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing audio-features endpoint")
    print(f"Token length: {len(token)}")
    print(f"Token prefix: {token[:20]}...")
    print(f"Headers: {headers}")
    
    response = requests.get(url, headers=headers)
    print(f"Audio features status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return {
        "status": response.status_code,
        "response": response.json() if response.status_code == 200 else response.text,
        "token_format_ok": token.startswith("BQ"),
        "note": "Spotify blocks audio-features in development mode. Using fallback in /recommend endpoint."
    }


@app.get("/callback")
def callback(code: str = Query(...)):
    """Handle Spotify callback and exchange code for token"""
    url = "https://accounts.spotify.com/api/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" in result:
        access_token = result["access_token"]
        # Store token
        user_tokens["current_user"] = access_token
        return JSONResponse({"message": "Login successful!", "token": access_token})
    else:
        return JSONResponse({"error": "Failed to get access token"}, status_code=400)


class SongRequest(BaseModel):
    song_name: str


@app.post("/recommend")
def recommend_song(request: SongRequest):
    """Get song recommendations with audio features"""
    token = user_tokens.get("current_user")
    
    if not token:
        return {"error": "Not authenticated. Visit /login first"}

    song_data = search_song(request.song_name, token)

    if not song_data:
        return {"error": "Song not found"}

    features = get_audio_features(song_data["id"], token)

    return {
        "input_song": song_data,
        "audio_features": features
    }


def search_song(song_name: str, token: str):
    """Search for a song on Spotify"""
    url = "https://api.spotify.com/v1/search"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": f'track:"{song_name}"',
        "type": "track",
        "limit": 1
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    if result.get("tracks", {}).get("items"):
        track = result["tracks"]["items"][0]

        return {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "spotify_url": track["external_urls"]["spotify"]
        }
    else:
        return None


def get_audio_features(track_id: str, token: str):
    """Get audio features for a track
    
    Note: Spotify's audio-features endpoint is restricted in development mode.
    Using track details as a workaround.
    """
    # Try the restricted audio-features endpoint first
    audio_url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(audio_url, headers=headers)
    
    # If we get audio features, return them
    if response.status_code == 200:
        result = response.json()
        if result and "danceability" in result:
            return {
                "danceability": result.get("danceability"),
                "energy": result.get("energy"),
                "tempo": result.get("tempo"),
                "valence": result.get("valence"),
                "acousticness": result.get("acousticness")
            }
    
    # Fallback: Use track details and return mock audio features
    # (Spotify development mode blocks audio-features endpoint)
    print(f"Audio-features endpoint returned {response.status_code}, using fallback data")
    
    track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
    response = requests.get(track_url, headers=headers)
    
    if response.status_code == 200:
        track = response.json()
        # Return mock audio features based on track popularity
        popularity = track.get("popularity", 50) / 100
        
        return {
            "danceability": min(0.9, popularity + 0.1),
            "energy": min(0.9, popularity + 0.2),
            "tempo": 80 + (popularity * 40),  # Mock tempo based on popularity
            "valence": min(0.9, popularity),
            "acousticness": max(0.1, 0.9 - popularity)
        }
    
    print(f"Failed to get audio features: {response.status_code}")
    return None