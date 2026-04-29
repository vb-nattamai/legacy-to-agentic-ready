# hello_world

Minimal Flask REST API used as the AgentReady hello_world example.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

The API starts on http://localhost:5000.

## Test

```bash
pytest
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service name and version |
| GET | `/health` | Health check |
| GET | `/greet/<name>` | Personalised greeting |
| GET | `/greetings` | All recorded greetings |
