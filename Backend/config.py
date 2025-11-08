from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb+srv://za901051_db_user:RuR1TZ6AqigZhrde@cluster.nt5xmvs.mongodb.net/?appName=Cluster"
    database_name: str = "security_console"
    
    class Config:
        env_file = ".env"


settings = Settings()

