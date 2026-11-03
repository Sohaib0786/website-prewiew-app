from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .database import Base, engine
from .routers import auth, sites

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Website Preview API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sites.router)

# Preview images. File names are random UUIDs, so they are not guessable.
app.mount("/previews", StaticFiles(directory=config.PREVIEW_DIR), name="previews")


@app.get("/api/health")
def health():
    return {"status": "ok"}
