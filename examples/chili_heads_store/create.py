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

be = be.BE(dbc)

with open('catalog.json', 'r') as fp:
    items = json.load(fp, encoding="ISO-8859-1")

print(items)
be.add_items(items)
print(be.get_item('SIEMENP_CAPBACC_LEMONDROP20'))
print(be.get_stock('SIEMENP_CAPBACC_LEMONDROP20'))

session_id = repr(uuid.uuid4())
basket = be.create_basket(session_id)

print(basket)
print(be.get_basket(session_id))
basket.add_item('SIEMENP_CAPBACC_LEMONDROP5', 10)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 1)
basket.add_item('SIEMENP_CAPBACC_LEMONDROP20', 19)

basket.dump(sys.stdout)

