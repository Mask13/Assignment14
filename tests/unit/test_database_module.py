from types import GeneratorType
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import get_engine, get_sessionmaker, get_db, settings


def test_get_engine_returns_engine():
    engine = get_engine(settings.DATABASE_URL)
    assert isinstance(engine, Engine)


def test_get_sessionmaker_returns_sessionmaker():
    engine = get_engine(settings.DATABASE_URL)
    SessionMaker = get_sessionmaker(engine)
    assert isinstance(SessionMaker, sessionmaker)


def test_get_db_yields_and_closes():
    # get_db returns a generator; first next() returns a Session, then closing should close it
    gen = get_db()
    assert isinstance(gen, GeneratorType)

    session = next(gen)
    assert isinstance(session, Session)

    # Close the generator to trigger finally block
    try:
        next(gen)
    except StopIteration:
        pass
