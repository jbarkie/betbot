from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    username = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    password = Column(String)