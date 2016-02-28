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
        return (item.code, item.description, item.long_description)

    def get_price(self, code):
        q = self.session.query(models.Item, models.Stock).\
          with_entities(models.Stock.price).\
          filter(models.Item.code == code).\
          filter(models.Item.id == models.Stock.item)
        price = q.first()
        if price is None:
            return None
        return price[0]

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
