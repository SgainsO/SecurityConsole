from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.connection import connect_to_mongo, close_mongo_connection
from routers.routes import router
from routers.message_routes import router as message_router
from routers.chat_routes import router as chat_router
from routers.conversation_routes import router as conversation_router
from routers.employee_routes import router as employee_router
from routers.admin_routes import router as admin_router


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
    title="Aiber - New Backend API",
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
app.include_router(message_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(employee_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Aiber - New Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

