import sqlalchemy as sqla
from sqlalchemy.engine.url import URL

import settings

def db_connect():
    return sqla.create_engine(URL(**settings.DB_ENGINE))
