# RAG (Retrieval-Augmented Generation) System

This project is a RAG system that lets you ingest documents and ask questions about them using AI.
Key Components:
- Ollama: Runs embedding (nomic-embed-text) and LLM (Mistral) locally
- PostgreSQL with pgvector: Stores document embeddings
- LangChain: Orchestrates the RAG pipeline

**How it works:**
1. Document ingestion (ingest.py): Loads markdown files, splits them, generates embeddings with Ollama, and stores vectors in PostgreSQL.

2. Querying (query.py): Takes a question, retrieves relevant chunks from the vector database, and uses Mistral to generate answers.

**Supported documents**: Markdown, PDF, Text, and more comming...

Use case: Build a local Q&A system over your documents without external APIs. Useful for internal documentation, knowledge bases, or any text you want to search and query with AI.
The system runs locally via Docker containers, keeping all data on your machine.

## Requirements

- Docker compose
- Python

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

Ingest the database with a markdown file

```sh
python .\app\ingest.py \path\to\file.md
```

Ask a question

```sh
python .\app\query.py "Yor question"
```