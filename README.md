## Requirements

- Docker compose
- Python

## Install

Build and run Ollama and Postgres containers

```sh
docker compose up -d 
```

Create a python virtual environment

```sh
python -m venv venv
```

Activate the environment

- On Linux/Mac

```sh
source venv/bin/activate
```

- On Windows

```sh
.\venv\Scripts\Activate
```

Install python dependencies

```sh
pip install -r requirements.txt
```