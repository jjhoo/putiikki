import sqlalchemy as sqla
from sqlalchemy import Column, Boolean, DateTime, Integer, Numeric, String, \
    CheckConstraint, ForeignKey, UniqueConstraint

from sqlalchemy.ext.declarative import declarative_base

# varchar or text type? no truncation with text, common enough?
from sqlalchemy.dialects.postgresql import TEXT

import datetime

Base = declarative_base()

class Catalog(Base):
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    code = Column(TEXT, nullable=False, unique=True)

    # descriptions could be in a separate table
    # (language, short_description, description)
    description = Column(TEXT, nullable=False)
    long_description = Column(TEXT, nullable=True)

    __table_args__ = (CheckConstraint('char_length(code) >= 4'),
                      CheckConstraint('char_length(description) >= 4'),)

class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    item = Column(Integer,
                  ForeignKey("catalog.id",
                             onupdate="CASCADE", ondelete="CASCADE"),
                  nullable=False)
    count = Column(Integer, nullable=False)
    price = Column(Numeric(12,2), nullable=False)
    visible = Column(Boolean, default=True, nullable=False)

    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    __table_args__ = (CheckConstraint('count >= 0'),
                      CheckConstraint('price >= 0.0'), )

class Basket(Base):
    __tablename__ = 'basket'
    id = Column(Integer, primary_key=True)
    # session cookie
    session = Column(TEXT, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

class BasketItems(Base):
    __tablename__ = 'basket_items'
    id = Column(Integer, primary_key=True)
    basket = Column(Integer,
                    ForeignKey("basket.id",
                                onupdate="CASCADE", ondelete="CASCADE"),
                    nullable=False)
    item = Column(Integer,
                  ForeignKey("catalog.id",
                             onupdate="CASCADE", ondelete="CASCADE"),
                  nullable=False)
    # count may be larger then reserved count
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    __table_args__ = (CheckConstraint('count >= 0'),)

class Reservations(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    item = Column(Integer,
                  ForeignKey("stock.id",
                             onupdate="CASCADE", ondelete="CASCADE"),
                  nullable=False)
    basket = Column(Integer,
                    ForeignKey("basket.id",
                               onupdate="CASCADE", ondelete="CASCADE"),
                    nullable=False)
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    __table_args__ = (CheckConstraint('count >= 0'),
                      UniqueConstraint('item', 'basket'))

def create_tables(engine):
    Base.metadata.create_all(engine)

def drop_tables(engine):
    Base.metadata.drop_all(engine)
