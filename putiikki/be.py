import sqlalchemy as sqla

from sqlalchemy.sql import func

from sqlalchemy.orm.session import Session
from sqlalchemy.engine.url import URL

from . import models

def db_connect(settings):
    return sqla.create_engine(URL(**settings['DB_ENGINE']))

class BE(object):
    def __init__(self, engine):
        self.engine = engine
        self.session = Session(bind=self.engine)

    def add_item(self, code, description, long_description):
        citem = models.Item(code=code,
                            description=description,
                            long_description=long_description)
        self.session.add(citem)
        return citem

    def add_category(self, name):
        cater = models.Category(name=name)
        self.session.add(cater)
        return cater

    def add_item_category(self, item_id, category_id, primary=False):
        catitem = models.ItemCategory(item=item_id, category=category_id,
                                      primary=primary)
        self.session.add(catitem)
        return catitem

    def get_item(self, code):
        q = self.session.query(models.Item).\
          filter(models.Item.code == code)
        item = q.first()
        if item is None:
            return None
        return (item.id, item.code, item.description, item.long_description)

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

        if q.count() == 0:
            stock = models.Stock(item=item_id, count=count, price=price)
            self.session.add(stock)
        else:
            stock = q.first()
            stock.count += count
            stock.price = price

    def add_items(self, items):
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

    # Basket related methods
    def create_basket(self, session):
        basket = models.Basket(session=session)
        self.session.add(basket)
        self.session.flush()
        self.session.refresh(basket)
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

        reservation = self.get_reservation(stock_id)
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

    def get_reservation(self, stock_id):
        q = self.be.session.query(models.Stock, models.Basket, models.BasketItem, models.Reservation).\
          with_entities(models.Reservation).\
          filter(models.Stock.id == stock_id).\
          filter(models.Stock.id == models.BasketItem.stock).\
          filter(models.BasketItem.id == models.Reservation.basket_item)
        res = q.first()
        return res

    def dump(self, fp):
        q = self.be.session.query(
            models.Item, models.Stock, models.Basket, models.BasketItem, models.Reservation).\
            with_entities(models.Item.description, models.Stock.price, models.Stock.count, models.BasketItem.count, models.Reservation.count).\
            filter(models.Basket.id == self.id).\
            filter(models.Basket.id == models.BasketItem.basket).\
            filter(models.Stock.id == models.BasketItem.stock).\
            filter(models.Item.id == models.Stock.item).\
            filter(models.BasketItem.id == models.Reservation.basket_item)
        for x in q:
            fp.write(repr(x) + "\n")
