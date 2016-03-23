import unittest

import sys
import os
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("../"))

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

from putiikki import be, models

import json
import uuid

class Simple(unittest.TestCase):
    def setUp(self):
        settings = { "DB_ENGINE" : { "drivername": "postgresql",
                                     "database": "putiikki" } }
        eng = be.db_connect(settings)
        models.drop_tables(eng)
        models.create_tables(eng)
        self.eng = eng

    def test_create_catalog(self):
        models.drop_tables(self.eng)
        models.create_tables(self.eng)
        catalog = be.Catalog(self.eng)

        with open(os.path.join(MODULE_DIR, 'shop_catalog1.json'), 'r',
                  encoding="ISO-8859-1") as fp:
            items = json.load(fp, encoding="ISO-8859-1")
            catalog.add_items_with_stock(items)
        catalog.session.commit()

    def test_long_success(self):
        models.drop_tables(self.eng)
        models.create_tables(self.eng)
        catalog = be.Catalog(self.eng)

        with open(os.path.join(MODULE_DIR, 'shop_catalog1.json'), 'r',
                  encoding="ISO-8859-1") as fp:
            items = json.load(fp, encoding="ISO-8859-1")
            catalog.add_items_with_stock(items)

        catalog.get_item('SIEMENP_CAPBACC_LEMONDROP20')
        catalog.get_stock('SIEMENP_CAPBACC_LEMONDROP20')

        items = catalog.list_items('description', ascending=True,
                                   page=1, page_size=5)
        items = catalog.list_items('description', ascending=True,
                                   page=2, page_size=5)
        items = catalog.search_items(prefix='Aji', price_range=(0.0, 2.0),
                                     sort_key='price', ascending=True,
                                     page=1, page_size=50)
        items = catalog.search_items(prefix='', price_range=(2.0, 5.0),
                                     sort_key='price', ascending=True,
                                     page=1, page_size=50)
        items = catalog.list_items_by_prices(prices=[('<', 2.0),
                                                     ('range', 2.0, 4.99),
                                                     ('>=', 5.0)],
                                             sort_key='price', ascending=True,
                                             page=1, page_size=50)
        session_id = str(uuid.uuid4())
        basket = be.Basket.create(catalog, session_id)

        basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 5)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 8)
        basket.add_item('SIEMENP_CAPANN_PADRON20', 1)
        basket.add_item('SIEMENP_CAPCHIN_NAGA5', 1)

        items = basket.list_items(sort_key='description', ascending=True)
        items = basket.list_items(sort_key='price', ascending=True)
        items = basket.list_items_by_prices(prices=[('>=', 2.0), ('<', 2.0)])

        session2_id = str(uuid.uuid4())
        basket2 = be.Basket.create(catalog, session2_id)
        basket2.add_item('SIEMENP_CAPBACC_LEMONDROP5', 16)
        basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
        basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)

        # catalog.remove_item('SIEMENP_CAPBACC_LEMONDROP5')
        # catalog.update_item('SIEMENP_CAPBACC_LEMONDROP20', description="asdf")

        catalog.session.commit()

if __name__ == '__main__':
    unittest.main()
