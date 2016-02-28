from putiikki import be, models

settings = { "DB_ENGINE" : { "drivername": "postgres", "database": "putiikki"}}

dbc = be.db_connect(settings)
models.drop_tables(dbc)
models.create_tables(dbc)
