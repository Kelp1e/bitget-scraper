from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ARB(Base):
    __tablename__ = "ARB"

    id = Column(Integer, primary_key=True)

    token_symbol = Column(String)
    orders = Column(JSON)
    contracts = Column(JSON)
    change_5m = Column(Float)
