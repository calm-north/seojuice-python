"""
Flask integration with SEOJuice.

Demonstrates sync client setup, request-level suggestion injection with a
simple TTL cache, and template rendering with SEO context.

Requirements:
    pip install seojuice[flask] flask

Run:
    flask --app examples.flask_app run --reload
"""
from __future__ import annotations

import os
import time
from typing import Any

from flask import Flask, Response, g, render_template, request

from seojuice import SEOJuice
from seojuice.injection._fetcher import apply_suggestions, fetch_suggestions_sync


app = Flask(__name__)
app.config["SEOJUICE_API_KEY"] = os.environ["SEOJUICE_API_KEY"]
app.extensions["seojuice"] = SEOJuice(app.config["SEOJUICE_API_KEY"])

# Simple TTL cache: url -> (data, expires_at)
_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 300.0  # 5 minutes


def _get_cached(url: str) -> dict | None:
    entry = _cache.get(url)
    if entry and entry[1] > time.monotonic():
        return entry[0]
    _cache.pop(url, None)
    return None


def _set_cached(url: str, data: dict) -> None:
    _cache[url] = (data, time.monotonic() + CACHE_TTL)


def _get_client() -> SEOJuice:
    return app.extensions["seojuice"]


@app.before_request
def fetch_seo_suggestions() -> None:
    """Fetch SEO suggestions for the current request URL."""
    url = request.url
    cached = _get_cached(url)
    if cached:
        g.seo_suggestions = cached
        return

    suggestions = fetch_suggestions_sync(url, timeout=3.0)
    if suggestions:
        _set_cached(url, suggestions)
    g.seo_suggestions = suggestions


@app.after_request
def inject_seo_tags(response: Response) -> Response:
    """Inject SEO meta tags into HTML responses."""
    if response.content_type and "text/html" not in response.content_type:
        return response

    suggestions = getattr(g, "seo_suggestions", None)
    if not suggestions:
        return response

    html = response.get_data(as_text=True)
    modified = apply_suggestions(html, suggestions)
    response.set_data(modified)
    return response


@app.route("/")
def index() -> str:
    client = _get_client()
    site = client.website("example.com")
    intel = site.intelligence(period="30d")
    return render_template("index.html", seo=intel)
