from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DB_URL
from app.models import Base, Record, VerificationEvent, AuditLog

engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)
