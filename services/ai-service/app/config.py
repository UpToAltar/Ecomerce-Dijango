import os


class Settings:
    PRODUCT_SERVICE_URL: str = os.getenv('PRODUCT_SERVICE_URL', 'http://product-service:8000')
    ORDER_SERVICE_URL: str = os.getenv('ORDER_SERVICE_URL', 'http://order-service:8000')
    REVIEW_SERVICE_URL: str = os.getenv('REVIEW_SERVICE_URL', 'http://review-service:8000')

    REDIS_HOST: str = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '2'))

    DATA_DIR: str = os.getenv('DATA_DIR', '/app/data')

    @property
    def MODEL_DIR(self) -> str:
        return f'{self.DATA_DIR}/models'

    @property
    def CHROMA_DIR(self) -> str:
        return f'{self.DATA_DIR}/chromadb'

    EMBEDDING_MODEL: str = 'paraphrase-multilingual-MiniLM-L12-v2'

    NCF_EMB_DIM: int = 64
    SEQ_EMB_DIM: int = 128
    LSTM_HIDDEN: int = 256
    TRAIN_EPOCHS: int = 15
    BATCH_SIZE: int = 256
    LEARNING_RATE: float = 0.001
    SEQ_LEN: int = 10

    CHAT_HISTORY_SIZE: int = 10
    CHAT_TTL_SECONDS: int = 3600
    BEHAVIOR_TTL_SECONDS: int = 86400


settings = Settings()
