from putiikki import models

dbc = models.db_connect()
models.drop_tables(dbc)
models.create_tables(dbc)
