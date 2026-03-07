import os
from sqlalchemy import create_engine, Column, Float, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# We might need to handle the password encoding if it has special characters, but SQLAlchemy 
# URL usually handles it if we create the URL object, or we can just expect a valid URL.
DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None
Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(Float, nullable=False)

class EquityHistory(Base):
    __tablename__ = "equity_history"
    date = Column(String, primary_key=True, index=True)
    equity = Column(Float, nullable=False)

def init_db():
    global engine, SessionLocal
    if not DATABASE_URL:
        print("DATABASE_URL not found. Database features will be disabled.")
        return
        
    try:
        # Create engine
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed to initialize database: {e}")

def get_db():
    if not SessionLocal:
        raise Exception("Database not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
