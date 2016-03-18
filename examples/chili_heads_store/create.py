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
from prettytable import PrettyTable

def print_items(items):
    table = PrettyTable(['description', 'price', 'count', 'reserved'])
    table.align = 'r'
    for item in items:
        table.add_row([item['description'], item['price'],
                       item['count'], item['reserved']])
    print(table)

def print_items_pg(items):
    table = PrettyTable(['price group', 'description', 'price', 'count',
                         'reserved'])
    table.align = 'r'
    for item in items:
        table.add_row([item['price_group'], item['description'],
                       item['price'], item['count'], item['reserved']])
    print(table)

def print_basket(items):
    table = PrettyTable(['description', 'price', 'count', 'reserved'])
    table.align = 'r'
    items = basket.list_items()
    for item in items:
        table.add_row([item['description'], item['price'],
                       item['count'], item['reserved']])
    print(table)

with open('settings.json', 'r') as fp:
    settings = json.load(fp, encoding="UTF-8")

print(settings)

dbc = be.db_connect(settings)
models.drop_tables(dbc)
models.create_tables(dbc)

catalog = be.Catalog(dbc)

with open('catalog.json', 'r', encoding="ISO-8859-1") as fp:
    items = json.load(fp, encoding="ISO-8859-1")

print(items)

# categories = set()
# for item in items:
#     for x in item['categories']:
#         categories.add(x)
# catalog.add_categories(categories)
# catalog.add_items(items)

# stock = [{'code': x['code'], 'count': x['count'],
#           'price': x['price']} for x in items]
# catalog.add_stock(stock)

# catalog.session.commit()
catalog.add_items_with_stock(items)

print(catalog.get_item('SIEMENP_CAPBACC_LEMONDROP20'))
print(catalog.get_stock('SIEMENP_CAPBACC_LEMONDROP20'))

print("page 1")
items = catalog.list_items('description', ascending=True, page=1, page_size=5)
print_items(items)

print("page 2")
items = catalog.list_items('description', ascending=True, page=2, page_size=5)
print_items(items)

print("by prefix and price range")
items = catalog.search_items(prefix='Aji', price_range=(0.0, 2.0),
                             sort_key='price', ascending=True,
                             page=1, page_size=50)
print_items(items)

items = catalog.search_items(prefix='', price_range=(2.0, 5.0),
                             sort_key='price', ascending=True,
                             page=1, page_size=50)
print_items(items)

print("by price groups")
items = catalog.list_items_by_prices(prices=[('<', 2.0), ('range', 2.0, 4.99),
                                              ('>=', 5.0)],
                                     sort_key='price', ascending=True,
                                     page=1, page_size=50)
print_items_pg(items)

session_id = str(uuid.uuid4())
print("Basket 1 %s" % session_id)
basket = be.Basket.create(catalog, session_id)

# print(basket)
# print(be.Basket.get(session_id))
basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 5)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 8)
basket.add_item('SIEMENP_CAPANN_PADRON20', 1)
basket.add_item('SIEMENP_CAPCHIN_NAGA5', 1)
print_basket(items)
print("")

print("Test basket item ordering")
items = basket.list_items(sort_key='description', ascending=True)
print_basket(items)
print("")

print("Test basket item ordering, by price")
items = basket.list_items(sort_key='price', ascending=True)
print_basket(items)
print("")

print("Test basket item ordering, by price groups")
items = basket.list_items_by_prices(prices=[('>=', 2.0), ('<', 2.0)])
print_basket(items)
print("")

session2_id = str(uuid.uuid4())
print("Basket 2 %s" % session2_id)
basket2 = be.Basket.create(catalog, session2_id)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP5', 16)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
print_basket(basket2.list_items())
print("")

print("Remove item from inventory")
print("")

catalog.remove_item('SIEMENP_CAPBACC_LEMONDROP5')
print("Basket 1 %s" % session_id)
print_basket(basket.list_items())
print("")

print("Basket 2 %s" % session2_id)
print_basket(basket2.list_items())
print("")

catalog.update_item('SIEMENP_CAPBACC_LEMONDROP20', description="asdf")
print("Basket 2 %s" % session2_id)
print_basket(basket.list_items())
print("")

catalog.session.commit()

print("list items")
items = catalog.list_items('description', ascending=True, page=1, page_size=50)
print_items(items)

print("by price groups")
items = catalog.list_items_by_prices(prices=[('<', 2.0), ('range', 2.0, 4.99),
                                              ('>=', 5.0)],
                                     sort_key='price', ascending=True,
                                     page=1, page_size=50)
print_items_pg(items)
