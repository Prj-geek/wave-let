"use client";

import { useState } from "react";

export default function Home() {
  const [song, setSong] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const recommend = async () => {
    if (!song) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/recommend?song=${encodeURIComponent(song)}`
      );
      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch {
      setError("Backend not reachable");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: 24 }}>
      <h1>Wave-let 🎧</h1>

      <input
        type="text"
        placeholder="Enter your favourite song"
        value={song}
        onChange={(e) => setSong(e.target.value)}
        style={{ padding: 8, width: 300 }}
      />

      <br /><br />

      <button onClick={recommend} disabled={loading}>
        {loading ? "Finding..." : "Recommend"}
      </button>

      <br /><br />

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <div>
          <h3>Recommended Song</h3>
          <p>
            <strong>{result.recommended_song}</strong> — {result.artist}
          </p>
          <a href={result.spotify_url} target="_blank">
            Open in Spotify
          </a>
        </div>
      )}
    </main>
  );
}

