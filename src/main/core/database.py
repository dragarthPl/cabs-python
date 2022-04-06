from functools import lru_cache
from typing import Iterator

from pydantic import BaseSettings

from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.future import Engine


class DBSettings(BaseSettings):
    """ Parses variables from environment on instantiation """
    database_uri: str

    class Config:
        env_file = 'dev.env'
        env_file_encoding = 'utf-8'


database_uri = DBSettings().database_uri
connect_args = {"check_same_thread": False}
engine = create_engine(database_uri, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_engine() -> Engine:
    return engine

def get_session() -> Session:
    with Session(engine) as session:
        yield session
