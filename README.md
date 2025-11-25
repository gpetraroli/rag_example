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