"""Configuration for ai-new-service."""
import os


class Settings:
    # Database (own Postgres)
    DB_HOST = os.getenv("DB_HOST", "postgres-ai-new")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "ai_new_db")
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Other services
    PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
    REVIEW_SERVICE_URL = os.getenv("REVIEW_SERVICE_URL", "http://review-service:8000")

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "3"))

    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpassword")

    # Model
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    DATA_DIR = os.getenv("DATA_DIR", "/app/data")
    MODELS_DIR = os.getenv("DATA_DIR", "/app/data") + "/models"
    PLOTS_DIR = os.getenv("DATA_DIR", "/app/data") + "/plots"

    # Training hyperparams
    EMBEDDING_DIM = 64
    HIDDEN_DIM = 128
    NUM_EPOCHS = 50
    BATCH_SIZE = 32
    LEARNING_RATE = 0.003
    SEQ_LENGTH = 5
    TRAIN_SPLIT = 0.8


settings = Settings()
