# coding: utf8
#

"""SQLAlchemy based management of a Web Shop catalog and Baskets: models"""

# Copyright (c) 2016 Jani J. Hakala <jjhakala@gmail.com> Jyväskylä, Finland
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, version 3 of the
#  License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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

    stock_item = relationship('StockItem', uselist=False,
                              back_populates='item')

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

class StockItem(Base):
    __tablename__ = 'stock_items'
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

    item = relationship('Item', back_populates='stock_item')
    basket_item = relationship('BasketItem', back_populates='stock_item')
    reservation = relationship("Reservation", back_populates="stock_item")

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
    stock_item_id = Column(Integer,
                           ForeignKey("stock_items.id",
                                      onupdate="CASCADE", ondelete="CASCADE"),
                           nullable=False)
    # count may be larger then reserved count
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    basket = relationship("Basket", back_populates="basket_items")
    reservation = relationship("Reservation", back_populates="basket_item")
    stock_item = relationship("StockItem", back_populates="basket_item")

    __table_args__ = (CheckConstraint('count >= 0'),
                      UniqueConstraint('basket_id', 'stock_item_id'))

class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    stock_item_id = Column(Integer,
                           ForeignKey("stock_items.id",
                                      onupdate="CASCADE", ondelete="CASCADE"),
                           nullable=False)
    basket_item_id = Column(Integer,
                            ForeignKey("basket_items.id",
                                       onupdate="CASCADE", ondelete="CASCADE"),
                            nullable=False)
    count = Column(Integer, nullable=False)

    creation = Column(DateTime, default=datetime.datetime.utcnow,
                      nullable=False)
    modification = Column(DateTime, default=datetime.datetime.utcnow,
                          nullable=False)

    basket_item = relationship("BasketItem", back_populates="reservation")
    stock_item = relationship("StockItem", back_populates="reservation")

    __table_args__ = (CheckConstraint('count >= 0'),
                      UniqueConstraint('stock_item_id', 'basket_item_id'))

def create_tables(engine):
    Base.metadata.create_all(engine)

def drop_tables(engine):
    Base.metadata.drop_all(engine)
