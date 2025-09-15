# Import all routes and start the server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.v1.jobs.webhook import router as jobs_router
from utils.logger import setup_logger

logger = setup_logger(__name__)
app = FastAPI(title="Code Eagle AI - Job Producer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
