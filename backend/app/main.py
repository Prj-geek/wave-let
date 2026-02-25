import requests
import base64
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def root():
  return {"message": "Wavelet API is running"}

#Request body model
class SongRequest(BaseModel):
  song_name: str

@app.post("/recommend")
def recommend_song(request: SongRequest):
  token = get_spotify_token()

  return {
    "input_song": request.song_name,
    "spotify_token_preview": token[:20]
  }

def get_spotify_token():
    client_id = "8969f7ba5dde4581ba4121d123298775"
    client_secret = "0ec67d1c9258433fa270183248207d91"

    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    result = requests.post(url, headers=headers, data=data)
    json_result = result.json()

    return json_result["access_token"]