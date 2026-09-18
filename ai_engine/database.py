from sqlalchemy import create_engine
import config


engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
    pool_recycle=1800,  # recycle connections after 30 min to avoid stale/leaked ones piling up
)
ai_engine = create_engine(
    config.AI_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_recycle=1800,
)