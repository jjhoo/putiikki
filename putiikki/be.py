# coding: utf8
#
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

from sqlalchemy.sql import func

from sqlalchemy.orm.session import Session
from sqlalchemy.engine.url import URL

from . import models

def db_connect(settings):
    return sqla.create_engine(URL(**settings['DB_ENGINE']),
                              isolation_level='SERIALIZABLE')

def ordering(q, ascending, sort_key):
    if ascending:
        order = sqla.asc
    else:
        order = sqla.desc

    if sort_key == 'description':
        q = q.order_by(order(models.Item.description))
    elif sort_key == 'price':
        q = q.order_by(order(models.Stock.price))
    else:
        raise ValueError("Invalid key")
    return q

def pg_ordering(q, ascending):
    if ascending:
        order = sqla.asc
    else:
        order = sqla.desc

    q = q.order_by('price_group').order_by(order(models.Stock.price))
    return q

def pagination(q, page, page_size):
    if page >= 1:
        q = q.limit(page_size).offset((page - 1) * page_size)
    else:
        raise ValueError("Invalid page")
    return q

class Catalog(object):
    def __init__(self, engine):
        self.engine = engine
        self.session = Session(bind=self.engine)

    def add_item(self, code, description, long_description=None):
        self.session.begin(subtransactions=True)
        citem = models.Item(code=code,
                            description=description,
                            long_description=long_description)
        self.session.add(citem)
        self.session.commit()
        return citem

    def add_category(self, name):
        self.session.begin(subtransactions=True)
        cater = models.Category(name=name)
        self.session.add(cater)
        self.session.commit()
        return cater

    # def remove_category
    # def rename_category

    def add_item_category(self, item_id, category_id, primary=False):
        self.session.begin(subtransactions=True)
        catitem = models.ItemCategory(item=item_id, category=category_id,
                                      primary=primary)
        self.session.add(catitem)
        self.session.commit()
        return catitem

    # def remove_item_category

    def get_item(self, code):
        q = self.session.query(models.Item).filter(models.Item.code == code)
        item = q.first()
        if item is None:
            return None
        return (item.id, item.code, item.description, item.long_description)

    def remove_item(self, code):
        self.session.begin(subtransactions=True)
        q = self.session.query(models.Item).filter(models.Item.code == code).\
          delete()
        self.session.commit()

    def update_item(self, code, description=None, long_description=None,
                    new_code=None):
        q = self.session.query(models.Item).filter(models.Item.code == code)
        item = q.first()

        self.session.begin(subtransactions=True)
        if new_code is not None:
            item.code = new_code

        if description is not None:
            item.description = description

        if long_description is not None:
            item.long_description = long_description
        self.session.commit()

    def get_stock(self, code):
        q = self.session.query(models.Item, models.Stock).\
          with_entities(models.Stock).\
          filter(models.Item.code == code).\
          filter(models.Item.id == models.Stock.item)
        res = q.first()
        if res is None:
            return None
        return (res.id, res.price, res.count)

    def update_stock(self, code, count, price, item_id=None):
        if item_id is not None:
            q = self.session.query(models.Item, models.Stock).\
              with_entities(models.Stock).\
              filter(models.Item.id == item_id).\
              filter(models.Item.id == models.Stock.item)
        else:
            q = self.session.query(models.Item, models.Stock).\
              with_entities(models.Stock).\
              filter(models.Item.code == code).\
              filter(models.Item.id == models.Stock.item)

        self.session.begin(subtransactions=True)
        if q.count() == 0:
            stock = models.Stock(item=item_id, count=count, price=price)
            self.session.add(stock)
        else:
            stock = q.first()
            stock.count += count
            stock.price = price
        self.session.commit()

    def add_items(self, items):
        self.session.begin(subtransactions=True)

        categories = []
        for item in items:
            # KeyErrors not caught if missing required field

            try:
                long_desc = item['long description']
            except KeyError:
                long_desc = None

            q = self.session.query(models.Item).\
              filter(models.Item.code == item['code'])

            if q.count() == 0:
                citem = self.add_item(item['code'],
                                      item['description'],
                                      long_desc)
                # needed to have up to date Id field
                self.session.flush()
                self.session.refresh(citem)
            else:
                citem = q.first()
            self.update_stock(item['code'], item['count'], item['price'],
                              citem.id)

            if 'categories' in item:
                categories.append((citem.id, item['categories']))

        for item_id, cats in categories:
            primary = True
            for cat in cats:
                q = self.session.query(models.Item, models.Category,
                                       models.ItemCategory).\
                  with_entities(models.Item).\
                  filter(models.Item.id == item_id).\
                  filter(models.Item.id == models.ItemCategory.item).\
                  filter(models.Category.id == models.ItemCategory.category).\
                  filter(models.Category.name == cat)

                if q.count() > 0:
                    primary = False
                    continue

                q = self.session.query(models.Category).\
                  filter(models.Category.name == cat)

                if q.count() == 0:
                    cater = self.add_category(cat)
                    self.session.flush()
                    self.session.refresh(cater)
                else:
                    cater = q.first()

                self.add_item_category(item_id, cater.id, primary)
                primary = False

        self.session.commit()

    def list_items(self, sort_key='description',
                   ascending=True, page=1, page_size=10):
        q = self.session.query(models.Item, models.Category,
                               models.ItemCategory, models.Stock).\
          with_entities(models.Item.code, models.Item.description,
                        models.Category.name, models.Stock.price,
                        models.Stock.count).\
          filter(models.Item.id == models.Stock.item).\
          filter(models.ItemCategory.item == models.Item.id).\
          filter(models.ItemCategory.category == models.Category.id).\
          filter(models.ItemCategory.primary == True)

        q = ordering(q, ascending, sort_key)
        q = pagination(q, page, page_size)

        res = [x for x in q]
        return res

    def search_items(self, prefix, price_range, sort_key='description',
                     ascending=True, page=1, page_size=10):
        q = self.session.query(models.Item, models.Category,
                               models.ItemCategory, models.Stock).\
          with_entities(models.Item.code, models.Item.description,
                        models.Category.name, models.Stock.price,
                        models.Stock.count).\
          filter(models.Stock.price.between(*price_range),
                 models.Item.id == models.Stock.item,
                 models.Item.description.like('{:s}%'.format(prefix)),
                 models.ItemCategory.item == models.Item.id,
                 models.ItemCategory.category == models.Category.id,
                 models.ItemCategory.primary == True)

        q = ordering(q, ascending, sort_key)
        q = pagination(q, page, page_size)

        res = [x for x in q]
        return res

    def list_items_by_prices(self, prices, sort_key='price', prefix=None,
                             ascending=True, page=1, page_size=10):
        # TODO: check if possible to group using SQL
        def start():
            q = self.session.query(models.Item,
                                   models.Category,
                                   models.ItemCategory,
                                   models.Stock).\
              with_entities(models.Item.code, models.Item.description,
                            models.Category.name, models.Stock.price,
                            models.Stock.count)
            if prefix is not None:
                q = q.filter(models.Item.description.like('{:s}%'.format(prefix)))
            return q

        def rest(q):
            q = q.filter(models.Item.id == models.Stock.item,
                         models.ItemCategory.item == models.Item.id,
                         models.ItemCategory.category == models.Category.id,
                         models.ItemCategory.primary == True)
            return q

        res = []
        for price_def in prices:
            q = start()
            if price_def[0] == '<':
                q = q.filter(models.Stock.price < price_def[1])
            elif price_def[0] == '<=':
                q = q.filter(models.Stock.price <= price_def[1])
            elif price_def[0] == '>':
                q = q.filter(models.Stock.price > price_def[1])
            elif price_def[0] == '>=':
                q = q.filter(models.Stock.price >= price_def[1])
            else:
                q = q.filter(models.Stock.price.between(*price_def))
            q = rest(q)
            q = ordering(q, ascending, sort_key)
            # may not work as intended?
            q = pagination(q, page, page_size)

            res2 = [x for x in q]
            res.append((price_def, res2))
        return res

    # Basket related methods
    def create_basket(self, session):
        self.session.begin(subtransactions=True)
        basket = models.Basket(session=session)
        self.session.add(basket)
        self.session.flush()
        self.session.refresh(basket)
        self.session.commit()

        self.session.commit()
        return Basket(self, basket.id)

    def get_basket(self, session):
        q = self.session.query(models.Basket).\
            filter(models.Basket.session == session)
        res = q.first()
        if res is None:
            return None

        return Basket(self, res.id)

    def get_reservations(self, stock_id):
        q = self.session.query(func.sum(models.Reservation.count)).\
          filter(models.Stock.id == stock_id).\
          filter(models.Stock.id == models.Reservation.stock)

        res = q.first()
        if res is None or res[0] is None:
            return 0

        return res[0]

class Basket(object):
    def __init__(self, be, basket_id):
        self.be = be
        self.id = basket_id

    def add_item(self, code, count):
        self.be.session.begin(subtransactions=True)

        item = self.be.get_item(code)
        if item is None:
            raise ValueError('Unknown code')
        item_id, code, _descr, _ = item

        stock = self.be.get_stock(code)
        if stock is None:
            raise ValueError('Not in stock')
        stock_id, price, scount = stock

        # Need to check if already in basket
        basket_item = self.get_item(stock_id)
        if basket_item is None:
            basket_item = models.BasketItem(basket=self.id, stock=stock_id,
                                            count=count)
            self.be.session.add(basket_item)
            self.be.session.flush()
            self.be.session.refresh(basket_item)
        else:
            basket_item.count += count

        reservations = self.be.get_reservations(stock_id)
        # can reserve (scount - reservations)

        reservation = self.get_reservation(basket_item.id)
        if reservation is not None:
            count += reservation.count
            rcount = min(count, scount - reservations + reservation.count)
            reservation.count = rcount
        else:
            rcount = min(count, scount - reservations)
            reservation = models.Reservation(stock=stock_id,
                                            basket_item=basket_item.id,
                                            count=rcount)
            self.be.session.add(reservation)
        self.be.session.commit()

    def get_item(self, stock_id):
        q = self.be.session.query(models.Stock, models.Basket, models.BasketItem).\
          with_entities(models.BasketItem).\
                  filter(models.Stock.id == stock_id).\
                  filter(models.Basket.id == self.id).\
                  filter(models.Basket.id == models.BasketItem.basket).\
                  filter(models.Stock.id == models.BasketItem.stock)
        res = q.first()
        return res

    def get_reservation(self, basket_item_id):
        q = self.be.session.query(models.Basket, models.BasketItem, models.Reservation).\
          with_entities(models.Reservation).\
          filter(models.BasketItem.id == basket_item_id).\
          filter(models.BasketItem.id == models.Reservation.basket_item)
        res = q.first()
        return res

    # def get_total -- return value of the basket

    def list_items(self, sort_key='description', ascending=True):
        q = self.be.session.query(
            models.Item, models.Stock, models.Basket,
            models.BasketItem, models.Reservation).\
            with_entities(models.Item.description, models.Stock.price,
                          models.Stock.count, models.BasketItem.count,
                          models.Reservation.count).\
            filter(models.Basket.id == self.id,
                   models.Basket.id == models.BasketItem.basket,
                   models.Stock.id == models.BasketItem.stock,
                   models.Item.id == models.Stock.item,
                   models.BasketItem.id == models.Reservation.basket_item)
        q = ordering(q, ascending, sort_key)
        res = [x for x in q]
        return res

    def list_items_by_prices(self, prices, sort_key='price', prefix=None,
                             ascending=True):
        cases = []
        i = 1
        for price_def in prices:
            if price_def[0] == '<':
                case = (models.Stock.price < price_def[1], i)
            elif price_def[0] == '<=':
                case = (models.Stock.price <= price_def[1], i)
            elif price_def[0] == '>':
                case = (models.Stock.price > price_def[1], i)
            elif price_def[0] == '>=':
                case = (models.Stock.price >= price_def[1], i)
            else:
                case = (models.Stock.price.between(*price_def), i)
            cases.append(case)
            i += 1

        q = self.be.session.query(
            models.Item, models.Stock, models.Basket,
            models.BasketItem, models.Reservation).\
            with_entities(sqla.case(cases, else_ = 0).label('price_group'),
                          models.Item.description, models.Stock.price,
                          models.Stock.count, models.BasketItem.count,
                          models.Reservation.count).\
            filter(models.Basket.id == self.id,
                   models.Basket.id == models.BasketItem.basket,
                   models.Stock.id == models.BasketItem.stock,
                   models.Item.id == models.Stock.item,
                   models.BasketItem.id == models.Reservation.basket_item)
        q = pg_ordering(q, ascending)
        res = [x for x in q]
        return res

    def dump(self, fp):
        items = self.list_items()
        for x in items:
            fp.write(repr(x) + "\n")
