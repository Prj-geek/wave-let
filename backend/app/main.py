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
  return {
    "input_song": request.song_name,
    "recommended_song": "Mock Song"
  }