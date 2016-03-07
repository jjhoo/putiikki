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
import decimal

def json_handler(x):
    if isinstance(x, decimal.Decimal):
        return float(x)
    raise TypeError

json_options = { 'default': json_handler,
                 'check_circular': False,
                 'ensure_ascii': False,
                 'sort_keys': False }

def create_basket(be):
    session_id = str(uuid.uuid4())
    basket = be.create_basket(session_id)

    # print(basket)
    # print(be.get_basket(session_id))
    basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 5)
    basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
    basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
    basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 8)
    basket.add_item('SIEMENP_CAPANN_PADRON20', 1)
    basket.add_item('SIEMENP_CAPCHIN_NAGA5', 1)

    return session_id

def dispatch(be, json_cmd):
    if json_cmd['module'] == 'catalog':
        obj = be
    elif json_cmd['module'] == 'basket':
        obj = be.get_basket(json_cmd['session'])
    else:
        return {'status': 'error' , 'value': 'unknown module'}

    try:
        fun = getattr(obj, json_cmd['function'])
    except AttributeError:
        return {'status': 'error' , 'value': 'unknown function'}

    res = fun(**json_cmd['args'])
    # print(json.dumps(res, **json_options))
    return res

with open('examples/chili_heads_store/settings.json', 'r') as fp:
    settings = json.load(fp, encoding="UTF-8")

# print(settings)

dbc = be.db_connect(settings)
models.drop_tables(dbc)
models.create_tables(dbc)

be = be.Catalog(dbc)

with open('examples/chili_heads_store/catalog.json', 'r') as fp:
    items = json.load(fp, encoding="ISO-8859-1")

# print(items)
be.add_items(items)
session = create_basket(be)

jcmd = { 'module': 'catalog', 'function': 'list_items',
         'args': {'sort_key': 'description', 'ascending': True,
                  'page': 1, 'page_size': 10 } }
print("JSON: " + json.dumps(jcmd))
print()

res = dispatch(be, jcmd)
print("JSON: " + json.dumps({'status': 'ok', 'value': res}, **json_options))
print()

jcmd = { 'module': 'basket', 'function': 'list_items', 'session': session,
         'args': {'sort_key': 'description', 'ascending': True } }
print("JSON: " + json.dumps(jcmd))
res = dispatch(be, jcmd)
print("JSON: " + json.dumps({'status': 'ok', 'value': res}, **json_options))
print()

# Fail
try:
    jcmd = { 'module': 'basket', 'function': 'list_items', 'session': session,
             'args': {'sort_key': 'description', 'ascending': True,
                      'page_size': 10} }
    print(json.dumps(jcmd))
    dispatch(be, jcmd)
except TypeError:
    print("Failed as intended")
    print("JSON: " + json.dumps({'status': 'error', 'value': 'unknown argument'}))
print()
