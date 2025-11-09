from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.connection import connect_to_mongo, close_mongo_connection
from routers.routes import router
from routers.message_routes import router as message_router
from routers.chat_routes import router as chat_router, initialize_chat_agent
from routers.conversation_routes import router as conversation_router
from routers.employee_routes import router as employee_router
from routers.admin_routes import router as admin_router
from routers.local_agent_routes import router as local_agent_router, initialize_local_agent
from routers.unified_agent_routes import router as unified_agent_router, initialize_unified_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("Starting New Backend API...")
    await connect_to_mongo()
    print("Connected to MongoDB")
    
    # Initialize Local Security Agent (standalone)
    try:
        initialize_local_agent()
    except Exception as e:
        print(f"Warning: Could not initialize Local Security Agent: {e}")
    
    # Initialize Chat Agent (local agent for employee chat)
    try:
        initialize_chat_agent()
        print("✓ Chat Agent (local) initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize Chat Agent: {e}")
    
    # Initialize Unified Agent (local + cloud workflow)
    try:
        initialize_unified_agent()
        print("✓ Unified Agent (local + cloud) initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize Unified Agent: {e}")
    
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
app.include_router(local_agent_router)
app.include_router(unified_agent_router)  # Main endpoint: /agent/process


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

