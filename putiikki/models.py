import sqlalchemy as sqla
from sqlalchemy import Column, Boolean, DateTime, Integer, Numeric, String, \
    CheckConstraint, ForeignKey, UniqueConstraint, TEXT, Table

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    code = Column(TEXT, nullable=False, unique=True)

    # descriptions could be in a separate table
    # (language, short_description, description)
    description = Column(TEXT, nullable=False)
    long_description = Column(TEXT, nullable=True)
    categories = relationship('ItemCategory')

    stock = relationship('Stock', uselist=False, back_populates='item')

    __table_args__ = (CheckConstraint('char_length(code) >= 4'),
                      CheckConstraint('char_length(description) >= 4'),)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(TEXT, nullable=False, unique=True)

    __table_args__ = (CheckConstraint('char_length(name) >= 4'),)

class ItemCategory(Base):
    __tablename__ = 'item_categories'
    item_id = Column(Integer,
                     ForeignKey("items.id",
                                onupdate="CASCADE", ondelete="CASCADE"),
                     primary_key=True)
    category_id = Column(Integer,
                         ForeignKey("categories.id",
                                    onupdate="CASCADE", ondelete="CASCADE"),
                         primary_key=True)
    primary = Column(Boolean, default=False, nullable=False)

    item = relationship("Item")
    category = relationship("Category")

    __table_args__ = (UniqueConstraint('item_id', 'category_id'),)

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer,
                     ForeignKey("items.id",
                                onupdate="CASCADE", ondelete="CASCADE"),
                     nullable=False, unique=True)
    count = Column(Integer, nullable=False)
    price = Column(Numeric(12,2), nullable=False)
    visible = Column(Boolean, default=True, nullable=False)

    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    item = relationship('Item', back_populates='stock')

    __table_args__ = (CheckConstraint('count >= 0'),
                      CheckConstraint('price >= 0.0'), )

class Basket(Base):
    __tablename__ = 'basket'
    id = Column(Integer, primary_key=True)
    # session cookie... could be a reference to Session table
    session = Column(TEXT, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    basket_items = relationship("BasketItem", back_populates="basket")

class BasketItem(Base):
    __tablename__ = 'basket_items'
    id = Column(Integer, primary_key=True)
    basket_id = Column(Integer,
                       ForeignKey("basket.id",
                                  onupdate="CASCADE", ondelete="CASCADE"),
                       nullable=False)
    stock = Column(Integer,
                   ForeignKey("stocks.id",
                              onupdate="CASCADE", ondelete="CASCADE"),
                   nullable=False)
    # count may be larger then reserved count
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    basket = relationship("Basket", back_populates="basket_items")

    __table_args__ = (CheckConstraint('count >= 0'),
                      UniqueConstraint('basket_id', 'stock'))

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    stock = Column(Integer,
                   ForeignKey("stocks.id",
                              onupdate="CASCADE", ondelete="CASCADE"),
                   nullable=False)
    basket_item = Column(Integer,
                         ForeignKey("basket_items.id",
                                    onupdate="CASCADE", ondelete="CASCADE"),
                         nullable=False)
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    __table_args__ = (CheckConstraint('count >= 0'),
                      UniqueConstraint('stock', 'basket_item'))

def create_tables(engine):
    Base.metadata.create_all(engine)

def drop_tables(engine):
    Base.metadata.drop_all(engine)
