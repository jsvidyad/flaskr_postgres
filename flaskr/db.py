from typing import List, Dict, Any
import os
import psycopg2
from psycopg2 import extras
from flask import g, Flask
import click

DBNAME = 'flask_tutorial'
HOST = '127.0.0.1'
USER = 'jvidyad'

class DBConnector:
    def __init__(self, dbname=DBNAME, host=HOST, user=USER):
        conn = psycopg2.connect(dbname=dbname, host=host, user=user)
        self.cursor = conn.cursor(cursor_factory=extras.DictCursor)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]] | None:
        self.cursor.execute(query)
        data = self.cursor.fetchall() if query.lstrip().lower().startswith('select') else None
        data = [dict(x) for x in data] if data is not None else data
        self.cursor.connection.commit()
        return data
        
    def close(self) -> None:
        self.cursor.close()
        self.cursor.connection.close()
        
def close_db(e=None) -> None:
    db = g.pop('db', None)
    
    if db is not None:
        db.close()
        

    
@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    