from motor.motor_asyncio import AsyncIOMotorClient
from config.config import settings


class Database:
    client: AsyncIOMotorClient = None
    
    
db = Database()


# Retrieve Database client
async def get_database():
    return db.client[settings.DATABASE_NAME]

# Establish connection to database client
async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_STRING)
    
# Close mongodb connection
async def close_mongo_connection():
    db.client.close()
