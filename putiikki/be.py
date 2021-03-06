# coding: utf8
#

"""SQLAlchemy based management of a Web Shop catalog and Baskets"""

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

__all__ = ['db_connect', 'Catalog', 'Basket']

def db_connect(settings):
    return sqla.create_engine(URL(**settings['DB_ENGINE']),
                              isolation_level='SERIALIZABLE')

def ordering(q, ascending, sort_key):
    if ascending:
        order = sqla.asc
    else:
        order = sqla.desc

    if sort_key == 'description':
        q = q.order_by(order(models.Item.description_lower))
    elif sort_key == 'price':
        q = q.order_by(order(models.StockItem.price))
    else:
        raise ValueError("Invalid key")
    return q

def pg_cases(prices):
    cases = []
    i = 0
    for price_def in prices:
        op = price_def[0]
        a = price_def[1]
        if op == '<':
            case = (models.StockItem.price < a, i)
        elif op == '<=':
            case = (models.StockItem.price <= a, i)
        elif op == '>':
            case = (models.StockItem.price > a, i)
        elif op == '>=':
            case = (models.StockItem.price >= a, i)
        elif op == '==':
            case = (models.StockItem.price == a, i)
        elif op == 'range':
            case = (models.StockItem.price.between(a, price_def[2]), i)
        cases.append(case)
        i += 1
    return cases

def pg_ordering(q, ascending):
    if ascending:
        order = sqla.asc
    else:
        order = sqla.desc

    q = q.order_by(sqla.asc('price_group')).\
      order_by(order(models.StockItem.price)).\
      order_by(sqla.asc(models.Item.description_lower))
    return q

def pagination(q, page, page_size):
    if page >= 1:
        q = q.limit(page_size).offset((page - 1) * page_size)
    else:
        raise ValueError("Invalid page")
    return q

def item_to_json(code, description, category, price, count, reserved=-1):
    x = {'code': code, 'description': description,
         'category': category, 'price': price, 'count': count}
    if reserved is None:
        x['reserved'] = 0
    else:
        x['reserved'] = reserved
    return x

def subtransaction(fun):
    def new_fun(self, *args, **kw):
        self.session.begin(subtransactions=True)

        try:
            res = fun(self, *args, **kw)
        except Exception as exc:
            self.session.rollback()
            raise exc

        self.session.commit()

        return res

    return new_fun

class Catalog(object):
    def __init__(self, engine):
        self.engine = engine
        self.session = Session(bind=self.engine)

    @subtransaction
    def add_item(self, code, description, long_description=None):
        citem = models.Item(code=code,
                            description=description,
                            long_description=long_description)
        self.session.add(citem)
        return citem

    @subtransaction
    def add_items(self, items):
        for item in items:
            # KeyErrors not caught if missing required field

            try:
                long_desc = item['long description']
            except KeyError:
                long_desc = None

            citem = models.Item(code=item['code'],
                                description=item['description'],
                                description_lower=item['description'].lower(),
                                long_description=long_desc)

            primary=True
            for cat in item['categories']:
                q = self.session.query(models.Category).\
                  filter(models.Category.name == cat)
                cater = q.first()

                icater = models.ItemCategory(item=citem, category=cater,
                                             primary=primary)
                citem.categories.append(icater)
                primary=False
            self.session.add(citem)

    def add_category(self, name):
        self.add_categories([name])

    @subtransaction
    def add_categories(self, names):
        for name in names:
            cater = models.Category(name=name)
            self.session.add(cater)

    # def remove_category: should make sure that zero use
    # def rename_category

    @subtransaction
    def add_item_category(self, item_id, category_id, primary=False):
        catitem = models.ItemCategory(item_id=item_id, category_id=category_id,
                                      primary=primary)
        self.session.add(catitem)
        return catitem

    # def remove_item_category

    def get_item(self, code, as_object=False):
        q = self.session.query(models.Item).filter(models.Item.code == code)
        item = q.first()
        if item is None:
            return None
        if as_object is True:
            return item
        return (item.id, item.code, item.description, item.long_description)

    def remove_item(self, code):
        self.session.begin(subtransactions=True)
        q = self.session.query(models.Item).filter(models.Item.code == code).\
          delete()
        self.session.commit()

    @subtransaction
    def update_item(self, code, description=None, long_description=None,
                    new_code=None):
        q = self.session.query(models.Item).filter(models.Item.code == code)
        item = q.first()

        if new_code is not None:
            item.code = new_code

        if description is not None:
            item.description = description
            item.description_lower = description.lower()

        if long_description is not None:
            item.long_description = long_description

    def get_stock(self, code, as_object=False):
        q = self.session.query(models.Item, models.StockItem).\
          with_entities(models.StockItem).\
          filter(models.Item.code == code).\
          filter(models.Item.id == models.StockItem.item_id)
        res = q.first()
        if res is None:
            return None

        if as_object is True:
            return res
        return (res.id, res.price, res.count)

    @subtransaction
    def add_stock(self, items):

        for item in items:
            q = self.session.query(models.Item).\
              filter(models.Item.code == item['code'])

            citem = q.first()
            stock = models.StockItem(item=citem, count=item['count'],
                                    price=item['price'])
            self.session.add(stock)

    @subtransaction
    def update_stock(self, code, count, price):
        q = self.session.query(models.Item, models.StockItem).\
              with_entities(models.StockItem).\
              join(models.StockItem.item).\
              filter(models.Item.code == code)

        stock = q.first()
        if stock is None:
            q = self.session.query(models.Item).\
              filter(models.Item.code == code)
            item = q.first()
            if item is not None:
                stock = models.StockItem(item=item, count=count, price=price)
                self.session.add(stock)
            else:
                raise KeyError('Unknown item code')
        else:
            stock.count += count
            stock.price = price

    @subtransaction
    def add_items_with_stock(self, items):
        categories = set()
        for item in items:
            for x in item['categories']:
                categories.add(x)
        self.add_categories(categories)

        self.add_items(items)
        self.add_stock(items)

    def list_items(self, sort_key='description',
                   ascending=True, page=1, page_size=10):
        sq = self.session.query(models.Reservation.stock_item_id,
                                func.sum(models.Reservation.count).\
                                label('reserved')).\
                                group_by(models.Reservation.stock_item_id).\
                                subquery()
        q = self.session.query(models.Item, models.Category,
                               models.ItemCategory, models.StockItem,
                               sq.c.reserved).\
          with_entities(models.Item.code, models.Item.description,
                        models.Category.name, models.StockItem.price,
                        models.StockItem.count, sq.c.reserved).\
          join(models.StockItem).\
          join(models.ItemCategory,
               models.Item.id == models.ItemCategory.item_id).\
          join(models.Category,
               models.Category.id == models.ItemCategory.category_id).\
          filter(models.ItemCategory.primary == True).\
          outerjoin(sq, models.StockItem.id == sq.c.stock_item_id)

        q = ordering(q, ascending, sort_key)
        q = pagination(q, page, page_size)

        res = [item_to_json(*x) for x in q]
        return res

    def search_items(self, prefix, price_range, sort_key='description',
                     ascending=True, page=1, page_size=10):
        sq = self.session.query(models.Reservation.stock_item_id,
                                func.sum(models.Reservation.count).\
                                label('reserved')).\
                                group_by(models.Reservation.stock_item_id).\
                                subquery()

        q = self.session.query(models.Item, models.Category,
                               models.ItemCategory, models.StockItem,
                               sq.c.reserved).\
          with_entities(models.Item.code, models.Item.description,
                        models.Category.name, models.StockItem.price,
                        models.StockItem.count,
                        sq.c.reserved).\
          join(models.StockItem).\
          join(models.ItemCategory,
               models.Item.id == models.ItemCategory.item_id).\
          join(models.Category,
               models.Category.id == models.ItemCategory.category_id).\
          filter(models.StockItem.price.between(*price_range),
                 models.Item.description_lower.like('{:s}%'.format(prefix.lower())),
                 models.ItemCategory.primary == True).\
          outerjoin(sq, models.StockItem.id == sq.c.stock_item_id)

        q = ordering(q, ascending, sort_key)
        q = pagination(q, page, page_size)

        res = [item_to_json(*x) for x in q]
        return res

    def list_items_by_prices(self, prices, sort_key='price', prefix=None,
                             ascending=True, page=1, page_size=10):
        pgs = pg_cases(prices)
        pg_case = sqla.case(pgs, else_ = -1).label('price_group')

        sq = self.session.query(models.Reservation.stock_item_id,
                                func.sum(models.Reservation.count).\
                                label('reserved')).\
                                group_by(models.Reservation.stock_item_id).\
                                subquery()

        q = self.session.query(models.Item, models.Category,
                               models.ItemCategory, models.StockItem,
                               sq.c.reserved).\
                               with_entities(pg_case, models.Item.code,
                                             models.Item.description,
                                             models.Category.name,
                                             models.StockItem.price,
                                             models.StockItem.count,
                                             sq.c.reserved)
        if prefix is not None:
            q = q.filter(models.Item.description_lower.like('{:s}%'.format(prefix.lower())))

        q = q.join(models.StockItem.item).\
          outerjoin(sq, models.StockItem.id == sq.c.stock_item_id).\
          filter(models.ItemCategory.item_id == models.Item.id,
                 models.ItemCategory.category_id == models.Category.id,
                 models.ItemCategory.primary == True,
                 pg_case >= 0)

        q = pg_ordering(q, ascending)
        q = pagination(q, page, page_size)
        def to_dict(x):
            tmp = item_to_json(*x[1:])
            tmp.update({'price_group': x[0]})
            return tmp
        res = [to_dict(x) for x in q]
        return res

    def _get_reservations(self, stock_id):
        q = self.session.query(func.sum(models.Reservation.count)).\
          filter(models.StockItem.id == stock_id).\
          filter(models.StockItem.id == models.Reservation.stock_item_id)

        res = q.first()
        if res is None or res[0] is None:
            return 0

        return res[0]

    def _get_reservation(self, basket_item_id):
        q = self.session.query(models.Basket, models.BasketItem,
                               models.Reservation).\
          with_entities(models.Reservation).\
          join(models.Reservation.basket_item).\
          filter(models.BasketItem.id == basket_item_id)
        res = q.first()
        return res

    @subtransaction
    def _update_reservation(self, stock, basket_item):
        reservations = self._get_reservations(basket_item.stock_item_id)
        # can reserve (scount - reservations)
        reservation = self._get_reservation(basket_item.id)

        if reservation is not None:
            rcount = min(basket_item.count,
                         stock.count - reservations + reservation.count)
            reservation.count = rcount
        else:
            rcount = min(basket_item.count, stock.count - reservations)
            reservation = models.Reservation(stock_item=stock,
                                             basket_item=basket_item,
                                             count=rcount)
            self.session.add(reservation)

class Basket(object):
    def __init__(self, catalog, basket_id):
        self.catalog = catalog
        self.session = catalog.session
        self.id = basket_id

    @staticmethod
    def get(catalog, basket_id):
        q = catalog.session.query(models.Basket).\
            filter(models.Basket.session == basket_id)
        res = q.first()
        if res is None:
            return None

        return Basket(catalog, res.id)

    @staticmethod
    def create(catalog, basket_id):
        session = catalog.session

        session.begin(subtransactions=True)
        basket = models.Basket(session=basket_id)
        session.add(basket)
        session.flush()
        session.refresh(basket)

        session.commit()
        return Basket(catalog, basket.id)

    @subtransaction
    def add_item(self, code, count):
        item = self.catalog.get_item(code, as_object=True)
        if item is None:
            raise ValueError('Unknown code')

        stock = self.catalog.get_stock(item.code, as_object=True)
        if stock is None:
            raise ValueError('Not in stock')

        # Need to check if already in basket
        basket_item = self.get_item(stock.id)
        if basket_item is None:
            basket_item = models.BasketItem(basket_id=self.id,
                                            stock_item=stock,
                                            count=count)
            self.session.add(basket_item)
            self.session.flush()
            self.session.refresh(basket_item)
        else:
            basket_item.count += count

        self.catalog._update_reservation(stock, basket_item)

    @subtransaction
    def update_item_count(self, code, count):
        item = self.catalog.get_item(code, as_object=True)
        if item is None:
            raise ValueError('Unknown item code')

        stock = self.catalog.get_stock(item.code, as_object=True)
        if stock is None:
            raise ValueError('Item {:s} not in stock'.format(item.code))

        basket_item = self.get_item(stock.id)
        if basket_item is None:
            raise ValueError('Item {:s} not in basket'.format(item.code))

        if count == 0:
            self.session.delete(basket_item)
            # Reservations are automatically deleted (on delete cascade)
            return

        basket_item.count = count
        self.catalog._update_reservation(stock, basket_item)

    def remove_item(self, code):
        return self.update_item_count(code, 0)

    def get_item(self, stock_id):
        q = self.session.query(models.StockItem, models.Basket,
                                  models.BasketItem).\
          with_entities(models.BasketItem).\
                  filter(models.StockItem.id == stock_id).\
                  filter(models.Basket.id == self.id).\
                  filter(models.Basket.id == models.BasketItem.basket_id).\
                  filter(models.StockItem.id == models.BasketItem.stock_item_id)
        res = q.first()
        return res

    # def get_total -- return value of the basket

    def list_items(self, sort_key='description', ascending=True):
        q = self.session.query(
            models.Item, models.StockItem, models.Basket,
            models.BasketItem, models.Reservation).\
            with_entities(models.Item.code, models.Item.description,
                          models.StockItem.price, models.BasketItem.count,
                          models.Reservation.count).\
            filter(models.Basket.id == self.id,
                   models.Basket.id == models.BasketItem.basket_id,
                   models.StockItem.id == models.BasketItem.stock_item_id,
                   models.Item.id == models.StockItem.item_id,
                   models.BasketItem.id == models.Reservation.basket_item_id)
        q = ordering(q, ascending, sort_key)
        def to_dict(x):
            return { 'code': x[0], 'description': x[1], 'price': x[2],
                     'count': x[3], 'reserved': x[4] }
        res = [to_dict(x) for x in q]
        return res

    def list_items_by_prices(self, prices, sort_key='price', prefix=None,
                             ascending=True):
        cases = pg_cases(prices)
        pg_case = sqla.case(cases, else_ = -1).label('price_group')

        q = self.session.query(
            models.Item, models.StockItem, models.Basket,
            models.BasketItem, models.Reservation).\
            with_entities(pg_case, models.Item.code,
                          models.Item.description, models.StockItem.price,
                          models.StockItem.count, models.BasketItem.count,
                          models.Reservation.count).\
            join(models.Basket.basket_items).\
            join(models.Item.stock_item).\
            filter(models.Basket.id == self.id,
                   models.StockItem.id == models.BasketItem.stock_item_id,
                   models.BasketItem.id == models.Reservation.basket_item_id,
                   pg_case >= 0)
        q = pg_ordering(q, ascending)
        def to_dict(x):
            return { 'price_group': x[0], 'code': x[1], 'description': x[2],
                     'price': x[3], 'count': x[4], 'reserved': x[5] }
        res = [to_dict(x) for x in q]
        return res

    def dump(self, fp):
        items = self.list_items()
        for x in items:
            fp.write(repr(x) + "\n")
