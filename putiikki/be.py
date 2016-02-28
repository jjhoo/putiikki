import sqlalchemy as sqla
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
        citem = models.Catalog(code=code,
                               description=description,
                               long_description=long_description)
        self.session.add(citem)
        return citem

    def update_stock(self, code, count, price, item_id=None):
        if item_id is not None:
            q = self.session.query(models.Catalog, models.Stock).\
              with_entities(models.Stock).\
              filter(models.Catalog.id == item_id).\
              filter(models.Catalog.id == models.Stock.item)
        else:
            q = self.session.query(models.Catalog, models.Stock).\
              with_entities(models.Stock).\
              filter(models.Catalog.code == code).\
              filter(models.Catalog.id == models.Stock.item)

        if q.count() == 0:
            stock = models.Stock(item=item_id, count=count, price=price)
            self.session.add(stock)
        else:
            stock = q.first()
            stock.count += count
            stock.price = price

    def add_to_catalog(self, items):
        for item in items:
            # KeyErrors not caught if missing required field

            try:
                long_desc = item['long description']
            except KeyError:
                long_desc = None

            q = self.session.query(models.Catalog).\
              filter(models.Catalog.code == item['code'])

            if q.count() == 0:
                citem = self.add_item(item['code'], item['description'],
                                      long_desc)
                # needed to have up to date Id field
                self.session.flush()
                self.session.refresh(citem)
            else:
                citem = q.first()
            self.update_stock(item['code'], item['count'], item['price'],
                              citem.id)
        self.session.commit()

    def get_item(self, code):
        q = self.session.query(models.Catalog).\
          filter(models.Catalog.code == code)
        item = q.first()
        return (item.code, item.description, item.long_description)

    def get_price(self, code):
        q = self.session.query(models.Catalog, models.Stock).\
          with_entities(models.Stock.price).\
          filter(models.Catalog.code == code).\
          filter(models.Catalog.id == models.Stock.item)
        price = q.first()
        return price[0]
