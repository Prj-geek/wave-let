🎵 Wave-let

Wave-let is a web-based music recommendation application that suggests songs closely matching a user’s favorite track. It uses similarity-based recommendation techniques on song metadata and audio features, and provides direct Spotify links for instant listening.

This project is built as a focused personal project to explore recommendation systems while maintaining a clean, scalable, and production-ready architecture.

🚀 Features

Input a favorite song to get a closely matched recommendation

Content-based similarity using genre, language, and audio features

Spotify integration for song previews and redirects

Modern web UI with fast API responses

Modular architecture for easy future expansion

🧠 How Recommendations Work

Wave-let uses a content-based recommendation approach:

Fetch metadata and audio features for the user’s favorite song

Compare it against a curated song dataset

Compute similarity using distance metrics (e.g., cosine similarity)

Return the most similar song along with its Spotify link

This approach does not require user history or collaborative filtering.

🛠 Tech Stack
Frontend

Next.js

TypeScript

Tailwind CSS

Backend

FastAPI (Python)

Recommendation Engine

Python (similarity-based logic)

Data

Spotify Web API

Curated song dataset