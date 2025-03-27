# Pass Predict Website

A website for predicting future satellite overpasses over a point on Earth.
It is intended to be user-friendly and mobile-friendly.
Anyone with a passing interest in satellite observing can use it to find good
viewing opportunities.

Backend API currently live at [api.passpredict.space](https://api.passpredict.space).

The satellite predictions are made with the [`passpredict`](https://pypi.org/project/passpredict/) Python package.


## Tech Stack

### Backend
* Python/FastAPI
* SQLAlchemy
* Hatchet Workflow Engine

### Frontend (Coming Soon)
* SvelteKit application

### Infrastructure
* Docker swarm cluster
* SQLite database
