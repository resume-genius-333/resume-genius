from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import resume, auth, jobs

app = FastAPI(title="Resume Genius API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(resume.router, prefix="/api/v1", tags=["resume"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])


@app.get("/")
async def root():
    return {"message": "Resume Genius API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}