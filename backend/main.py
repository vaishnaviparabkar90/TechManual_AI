
from fastapi import FastAPI

from backend.routers.manuals import router as manuals_router
from backend.routers.chat import router as chat_router

app = FastAPI(
    title="TechManual AI",
    description="A RAG assistant for technical product manuals.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to TechManual AI",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(manuals_router)
app.include_router(chat_router)
