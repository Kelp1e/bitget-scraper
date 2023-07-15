from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base


def get_engine():
    engine = create_engine("sqlite:///bitget.db")

    return engine


def create_session():
    engine = get_engine()
    session = sessionmaker(bind=engine)

    Base.metadata.create_all(engine)

    return session
