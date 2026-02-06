# backend/main.py

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Wave-let API")

# Allow frontend (Next.js) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Wave-let backend running"}


@app.get("/recommend")
def recommend(song: str = Query(..., description="User's favourite song")):
    """
    Temporary stub endpoint.
    Later this will:
    - Search song on Spotify
    - Extract audio features
    - Find similar songs
    """

    # Hardcoded response for now (MVP stub)
    return {
        "input_song": song,
        "recommended_song": "Save Your Tears",
        "artist": "The Weeknd",
        "spotify_url": "https://open.spotify.com/track/5QO79kh1waicV47BqGRL3g"
    }

