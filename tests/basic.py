import unittest

import sys
sys.path.append('..')
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

from putiikki import be, models

class Simple(unittest.TestCase):
    def setUp(self):
        settings = { "DB_ENGINE" : { "drivername": "postgresql",
                                     "database": "putiikki" } }
        eng = be.db_connect(settings)
        models.drop_tables(eng)
        models.create_tables(eng)
        self.eng = eng

    def test_create_catalog(self):
        import json
        catalog = be.Catalog(self.eng)
        with open(os.path.join(MODULE_DIR, 'shop_catalog1.json'), 'r') as fp:
            items = json.load(fp, encoding="ISO-8859-1")
            catalog.add_items(items)
