# main.py
from fastapi import FastAPI

from voting.routers import health, polls

# Initialize the main FastAPI application instance
app = FastAPI(title="voting")

# ####################
# routes
# ####################
# healthz/, readyz/
app.include_router(health.router)
# polls/
app.include_router(polls.router)
