from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from api.src.config import DB_URL

Base = declarative_base()

def connect_to_db():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session