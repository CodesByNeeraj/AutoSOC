from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

#grab the database url from env file
DATABASE_URL = os.getenv("NEON_CONNECTION_STRING")

#connect to postgres
# pool_pre_ping: test connection before use — prevents SSL drops from Neon's idle timeout
# pool_recycle: replace connections older than 5 minutes
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require", "connect_timeout": 10}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#incidents table
class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    severity = Column(String)
    status = Column(String, default="open")
    raw_log = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

#findings from each agent
class Finding(Base):
    __tablename__ = "findings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String)
    agent = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# final reports
class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()