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

with open('settings.json', 'r') as fp:
    settings = json.load(fp, encoding="UTF-8")

print(settings)

dbc = be.db_connect(settings)
models.drop_tables(dbc)
models.create_tables(dbc)

be = be.Catalog(dbc)

with open('catalog.json', 'r') as fp:
    items = json.load(fp, encoding="ISO-8859-1")

print(items)
be.add_items(items)
print(be.get_item('SIEMENP_CAPBACC_LEMONDROP20'))
print(be.get_stock('SIEMENP_CAPBACC_LEMONDROP20'))

print("page 1")
for x in be.list_items('description', ascending=True, page=1, page_size=5):
    print(x)

print("page 2")
for x in be.list_items('description', ascending=True, page=2, page_size=5):
    print(x)
print("")

print("by prefix and price range")
for x in be.search_items(prefix='Aji', price_range=(0.0, 2.0),
                         sort_key='price', ascending=True,
                         page=1, page_size=50):
    print(x)
print("")

for x in be.search_items(prefix='', price_range=(2.0, 5.0),
                         sort_key='price', ascending=True,
                         page=1, page_size=50):
    print(x)
print("")

print("by price groups")
res = be.list_items_by_prices(prices=[('<', 2.0), ('>=', 2.0)],
                              sort_key='price', ascending=True,
                              page=1, page_size=50)
for n, (x, y) in enumerate(res, 1):
    print('Price group {:d}'.format(n))
    for item in y:
        print(item)
    print("")
print("")

session_id = str(uuid.uuid4())
print("Basket 1 %s" % session_id)
basket = be.create_basket(session_id)

# print(basket)
# print(be.get_basket(session_id))
basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 5)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 8)
basket.add_item('SIEMENP_CAPANN_PADRON20', 1)
basket.add_item('SIEMENP_CAPCHIN_NAGA5', 1)

basket.dump(sys.stdout)
print("")

print("Test basket item ordering")
items = basket.list_items(sort_key='description', ascending=True)
for x in items:
    print(x)
print("")

print("Test basket item ordering, by price")
items = basket.list_items(sort_key='price', ascending=True)
for x in items:
    print(x)
print("")

session2_id = str(uuid.uuid4())
print("Basket 2 %s" % session2_id)
basket2 = be.create_basket(session2_id)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP5', 16)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket2.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket2.dump(sys.stdout)
print("")

be.remove_item('SIEMENP_CAPBACC_LEMONDROP5')
print("Basket 1 %s" % session_id)
basket.dump(sys.stdout)
print("")

print("Basket 2 %s" % session2_id)
basket2.dump(sys.stdout)
print("")

be.update_item('SIEMENP_CAPBACC_LEMONDROP20', description="asdf")
print("Basket 2 %s" % session2_id)
basket2.dump(sys.stdout)
print("")
