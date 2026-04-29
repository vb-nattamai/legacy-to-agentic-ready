"""Minimal Flask REST API — AgentReady hello_world example."""
from flask import Flask, jsonify

app = Flask(__name__)

# In-memory store — intentionally simple, no database
_greetings: list[dict] = []


@app.get("/")
def index():
    """Service root — returns name and version."""
    return jsonify({"service": "hello_world", "version": "0.1.0"})


@app.get("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@app.get("/greet/<name>")
def greet(name: str):
    """Return a personalised greeting and record it."""
    greeting = {"name": name, "message": f"Hello, {name}!"}
    _greetings.append(greeting)
    return jsonify(greeting)


@app.get("/greetings")
def list_greetings():
    """Return all recorded greetings."""
    return jsonify({"greetings": _greetings, "count": len(_greetings)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
