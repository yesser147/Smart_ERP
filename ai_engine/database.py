from sqlalchemy import create_engine
import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
ai_engine = create_engine(config.AI_DATABASE_URL)