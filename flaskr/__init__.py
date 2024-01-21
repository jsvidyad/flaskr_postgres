# The flask app factory

import os
from flask import Flask

def create_app(test_config=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        ...
    
    @app.route('/')
    def root():
        return 'Hello Everyone!!!'
    
    from . import auth, blog, db
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    db.init_app(app)
    
    return app
