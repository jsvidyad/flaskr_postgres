from flask import g

from .db import DBConnector

def get_db(**kwargs) -> DBConnector:
    if 'db' not in g:
        g.db = DBConnector(**kwargs)
    
    return g.db