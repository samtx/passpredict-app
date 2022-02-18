# Pass Predict Website

A website for predicting future satellite overpasses over a point on Earth.
It is intended to be user-friendly and mobile-friendly.
Anyone with a passing interest in satellite observing can use it to find good
viewing opportunities.

Currently live at [passpredict.com](https://passpredict.com).

The satellite predictions are made with the [`passpredict`](https://pypi.org/project/passpredict/) Python package.

## Passes public API endpoint

This web app exposes a public REST API for generating pass predictions.
Details on how to use the API can be [found here](app/templates/api-home.md).


## Tech Stack

### Backend (Python)
* Starlette
* FastAPI
* Databases
* SQLAlchemy Core

### Frontend
* Jinja templates
* Bulma styling
* Svelte components

### Infrastructure
* Docker container with gunicorn/uvicorn
* PostgreSQL database
* Redis cache


## Development

Use `pip-compile` to update frozen dependencies in `requirements.txt` based on `requirements.in`.
