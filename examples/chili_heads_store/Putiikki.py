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
from putiikki import be, models

import json
import uuid
import sys

from ladon.ladonizer import ladonize
from ladon.compat import PORTABLE_STRING
from ladon.types.ladontype import LadonType
from ladon.exceptions.service import ClientFault, ServerFault

class Item(LadonType):
    code = PORTABLE_STRING
    description = PORTABLE_STRING
    category = PORTABLE_STRING
    price = float
    count = int
    reserved = int

class GroupedItem(LadonType):
    group = int
    code = PORTABLE_STRING
    description = PORTABLE_STRING
    category = PORTABLE_STRING
    price = float
    count = int
    reserved = int

class BasketItem(LadonType):
    code = PORTABLE_STRING
    description = PORTABLE_STRING
    price = float
    count = int
    reserved = float

class PriceGroup(LadonType):
    a = float
    b = { 'type': float, 'nullable': True, 'default': -1.0 }
    op = PORTABLE_STRING

class Catalog(object):
    def __init__(self):
        with open('settings.json', 'r') as fp:
            settings = json.load(fp, encoding="UTF-8")

        self.dbc = be.db_connect(settings)
        # models.drop_tables(self.dbc)
        # models.create_tables(self.dbc)
        self.catalog = be.Catalog(self.dbc)

    @ladonize(rtype=int)
    def _create(self):
        with open('catalog.json', 'r', encoding="ISO-8859-1") as fp:
            items = json.load(fp, encoding="ISO-8859-1")
            print(items)
        self.catalog.add_items_with_stock(items)
        self.catalog.session.commit()
        return 0

    @ladonize(PORTABLE_STRING, bool, int, int, rtype=[Item])
    def list_items(self,
                   sort_key=PORTABLE_STRING('description'), ascending=True,
                   page=1, page_size=10):
        items = self.catalog.list_items(sort_key, ascending, page, page_size)
        def dummy(x):
            nx = Item()
            nx.code = x['code']
            nx.count = x['count']
            nx.category = x['category']
            nx.description = x['description']
            nx.price = float(x['price'])
            nx.reserved = x['reserved']
            return nx
        return [dummy(x) for x in items]

    @ladonize(PORTABLE_STRING, float, float, PORTABLE_STRING,
              bool, int, int, rtype=[Item])
    def search_items(self, prefix=PORTABLE_STRING(''),
                     price_min=0.0, price_max=10000.0,
                     sort_key=PORTABLE_STRING('price'), ascending=True,
                     page=1, page_size=10):
        items = self.catalog.search_items(prefix, (price_min, price_max),
                                     sort_key, ascending, page, page_size)
        def dummy(x):
            nx = Item()
            nx.code = x['code']
            nx.count = x['count']
            nx.category = x['category']
            nx.description = x['description']
            nx.price = float(x['price'])
            nx.reserved = x['reserved']
            return nx
        return [dummy(x) for x in items]

    @ladonize([PriceGroup], PORTABLE_STRING, PORTABLE_STRING,
              bool, int, int, rtype=[GroupedItem])
    def list_items_by_pg(self, prices,
                         sort_key='price', prefix=PORTABLE_STRING(''),
                         ascending=True, page=1, page_size=50):
        pgs = [(pg.op, pg.a, pg.b) for pg in prices]
        items = self.catalog.list_items_by_prices(pgs, sort_key, prefix,
                                             ascending, page, page_size)
        def dummy(x):
            nx = GroupedItem()
            nx.group = x['price_group']
            nx.code = x['code']
            nx.count = x['count']
            nx.category = x['category']
            nx.description = x['description']
            nx.price = float(x['price'])
            nx.reserved = x['reserved']
            return nx
        return [dummy(x) for x in items]

class Basket(object):
    def __init__(self):
        with open('settings.json', 'r') as fp:
            settings = json.load(fp, encoding="UTF-8")

        self.dbc = be.db_connect(settings)
        # models.drop_tables(self.dbc)
        # models.create_tables(self.dbc)
        self.catalog = be.Catalog(self.dbc)

    @ladonize(PORTABLE_STRING, rtype=int)
    def create_basket(self, session_id):
        basket = be.Basket.create(self.catalog, session_id)
        self.catalog.session.commit()
        return 0

    @ladonize(PORTABLE_STRING, rtype=int)
    def _stuff_basket(self, session_id):
        basket = be.Basket.get(self.catalog, session_id)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 16)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
        basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
        self.catalog.session.commit()

        return 0

    @ladonize(PORTABLE_STRING, PORTABLE_STRING, int, rtype=int)
    def add_item(self, session_id, code, count):
        basket = be.Basket.get(self.catalog, session_id)
        basket.add_item(code, count)
        self.catalog.session.commit()

        return 0

    @ladonize(PORTABLE_STRING, PORTABLE_STRING, bool, rtype=[BasketItem])
    def list_items(self, session_id, sort_key='description', ascending=True):
        basket = be.Basket.get(self.catalog, session_id)
        if basket is None:
            raise ClientFault('basket not found', detail=session_id)

        try:
            items = basket.list_items(sort_key, ascending)
        except ValueError as ex:
            raise ClientFault(str(ex), hint='invalid sort key',
                              detail=sort_key)

        def dummy(x):
            nx = BasketItem()
            nx.code = x['code']
            nx.count = x['count']
            nx.description = x['description']
            nx.price = float(x['price'])
            nx.reserved = float(x['reserved'])
            return nx
        return [dummy(x) for x in items]
