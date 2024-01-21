from flask import g, request, flash, redirect, url_for, Blueprint, render_template, session
from flask.typing import ResponseReturnValue
from flask.views import View
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

from .utils import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')
db = get_db()

class UserRegister(View):
    methods = ('GET', 'POST')
    init_every_request = False
    
    def dispatch_request(self) -> ResponseReturnValue:
        if request.method == 'POST':
            error = None
            username = request.form['username']
            password = request.form['password']
            if username is None:
                error = 'Username is Required.'
            elif password is None:
                error = 'Password is Required.'
            else:
                query = f'INSERT INTO users (username, password) VALUES ({username}, {generate_password_hash(password)})'
                global db
                try:
                    db.execute_query(query)
                except psycopg2.errors.UniqueViolation:
                    error = 'The username is taken. Please choose another one'
                else:
                    return redirect(url_for('auth.login'))
            flash(error)
            
        return render_template('auth/register.html')

class UserLogin(View):
    methods=('GET', 'POST')
    init_every_request = False
    
    def dispatch_request(self) -> ResponseReturnValue:
        error = None
        if request.method == 'POST':
            global db
            username = request.form['username']
            password = request.form['password']
            query = f'SELECT * FROM users WHERE username={username}'
            data = db.execute_query(query)
            db_password = data[0]['password']
            if len(data) == 0:
                error = 'Invalid username.'
            elif not check_password_hash(db_password, password):
                error = 'Invalid Password.'
            else:
                session.clear()
                session['user_id'] = data[0]['id']
                return redirect(url_for('index'))
            flash(error)
            
        return render_template('auth/login.html')
    
class UserDelete(View):
    methods = ('GET', 'POST')
    init_every_request = False
    DELETED_MESSAGE = 'User has been deleted.'
    
    def _delete_user(username: str) -> None:
        global db
        query1 = f'SELECT id FROM users WHERE username = {username};'
        data = db.execute_query(query1)
        author_id = data[0]['id']
        query2 = f'DELETE FROM posts WHERE author_id = {author_id};'
        db.execute_query(query2)
        query3 = f'DELETE FROM users WHERE username = {username};'
        db.execute_query(query3)
        session.clear()
            
    def dispatch_request(self) -> ResponseReturnValue:
        username = getattr(g, 'user', {}).get('username')
        error = None
        global db
        if username is not None:
            self._delete_user(username)
            error = type(self).DELETED_MESSAGE
        elif request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username is None:
                error = 'Username is required.'
            elif password is None:
                error = 'Password is required.'
            else:
                query = f'SELECT * FROM users WHERE username = {username};'
                data = db.execute_query(query)
                if len(data) == 0:
                    error = 'Username does not exist in the database. Try again.'
                elif check_password_hash(data[0]['password'], password):
                    self._delete_user(username)
                    error = type(self).DELETED_MESSAGE
                else:
                    error = 'Invalid password.'
        
        flash(error)
        return render_template('auth/delete.html', user=username)
    
class UserLogout(View):
    methods = ('GET',)
    init_every_request = False
    
    def dispatch_request(self) -> ResponseReturnValue:
        session.clear()
        return redirect(url_for('index'))

bp.add_url_rule('/register', view_func=UserRegister.as_view('register'))
bp.add_url_rule('/login', view_func=UserLogin.as_view('login'))
bp.add_url_rule('/delete', view_func=UserDelete.as_view('delete'))
bp.add_url_rule('/logout', view_func=UserDelete.as_view('logout'))

@bp.before_app_request
def load_logged_in_user():
    global db
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.execute_query(f'SELECT * FROM users WHERE id = {user_id};')[0]
