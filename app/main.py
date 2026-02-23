from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routes import auth, users, predictions, posts, social, chat

# Automatically create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve prediction uploads
import os
os.makedirs("static/uploads/predictions", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(predictions.router)
app.include_router(posts.router)
app.include_router(social.router)
app.include_router(chat.router)

from fastapi.responses import FileResponse

@app.get("/", tags=["Frontend"])
def serve_frontend():
    return FileResponse("static/index.html")
