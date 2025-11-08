from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.connection import connect_to_mongo, close_mongo_connection
from routers.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("Starting New Backend API...")
    await connect_to_mongo()
    print("Connected to MongoDB")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_mongo_connection()
    print("MongoDB connection closed")


app = FastAPI(
    title="Security Console - New Backend API",
    description="Backend API for processing prompts through the security agent and logging to database",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Security Console - New Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

