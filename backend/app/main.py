from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import proposals, tasks, teams
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Hack Alem AI API", lifespan=lifespan)
app.include_router(tasks.router)
app.include_router(proposals.router)
app.include_router(teams.router)
