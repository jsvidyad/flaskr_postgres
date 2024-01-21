import functools
from flask import g, redirect, url_for

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if getattr(g, 'user', None) is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    
    return wrapped_view
