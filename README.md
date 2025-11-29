# RAG (Retrieval-Augmented Generation) System

This project is a RAG system that lets you ingest documents and ask questions about them using AI.
Key Components:
- Ollama: Runs embedding (nomic-embed-text) and LLM (Mistral) locally
- PostgreSQL with pgvector: Stores document embeddings
- LangChain: Orchestrates the RAG pipeline

**How it works:**
1. Document ingestion (ingest.py): Loads markdown files, splits them, generates embeddings with Ollama, and stores vectors in PostgreSQL.

2. Querying (query.py): Takes a question, retrieves relevant chunks from the vector database, and uses Mistral to generate answers.

**Supported documents**: Markdown, PDF, Text, images (jpg, jpeg, png) and audio files (mp3, wav, m4a, ogg, flac).

> **Note:** <br />
> For audio files you need to install FFmpeg on your system: (https://www.ffmpeg.org/) <br />
> Audio files are processed with the `openai-whisper` library; this library will try to use your GPU (CUDA on Nvidia, MPS on Mac) automatically.
> - If you have a GPU: Transcription will be very fast (seconds/minutes).
> - If you are on CPU: Transcription will be slower (1x realtime or slower).

Use case: Build a local Q&A system over your documents without external APIs. Useful for internal documentation, knowledge bases, or any text you want to search and query with AI.
The system runs locally via Docker containers, keeping all data on your machine.

## Requirements

- Docker compose
- Python 3.10+

## Install

Build and run Ollama and Postgres containers

```sh
docker compose up -d 
```

Create the environment

- On Linux/Mac

```sh
python3 -m venv venv

source venv/bin/activate
```

- On Windows

```sh
python -m venv venv

.\venv\Scripts\Activate
```

Install python dependencies

```sh
pip install -r requirements.txt
```

## Usage

Ingest the database with a file

```sh
python .\app\ingest.py \path\to\file.md
```

Ask a question

```sh
python .\app\query.py "Yor question"
```