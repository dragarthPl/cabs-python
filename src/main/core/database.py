import logging
from contextlib import contextmanager, AbstractContextManager
from typing import Iterator, Callable

import injector
from injector import inject
from pydantic import BaseSettings
from sqlalchemy import orm
from sqlalchemy.future import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.sql.expression import Select, SelectOfScalar


logger = logging.getLogger(__name__)

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore


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

def drop_db_and_tables():
    Session(engine).close_all()
    SQLModel.metadata.drop_all(engine)

def get_engine() -> Engine:
    return engine

def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class DatabaseModule(injector.Module):

    def __init__(self) -> None:
        database_uri = DBSettings().database_uri
        connect_args = {"check_same_thread": False}
        self._engine = create_engine(database_uri, echo=True, connect_args=connect_args)

        self._session_factory = sessionmaker(bind=self._engine, future=True)

    def configure(self, _binder: injector.Binder) -> None:
        database_uri = DBSettings().database_uri
        connect_args = {"check_same_thread": False}
        self._engine = create_engine(database_uri, echo=True, connect_args=connect_args)
        self._session_factory = sessionmaker(class_=Session, bind=self._engine, future=True)

    def create_database(self) -> None:
        SQLModel.metadata.create_all(self._engine)

    @injector.singleton
    @injector.provider
    def session(self) -> Session:
        return self._session_factory()
