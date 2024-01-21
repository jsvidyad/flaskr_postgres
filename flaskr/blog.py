from typing import List, Dict, Any
from flask import g, views, render_template, Blueprint, request, flash, abort, redirect, url_for
from flask.typing import ResponseReturnValue

from .decorators import login_required
from .utils import get_db

bp = Blueprint('blog', __name__, url_prefix='/blog')
db = get_db()

class BlogIndexView(views.View):
    methods = ('GET',)
    init_every_request = False
    
    def _get_blogs(self) -> List[Dict[str, Any]]:
        query = 'SELECT p.id, title, body, created, username FROM posts p JOIN users u ON p.author_id=u.id ORDER BY created DESC;'
        global db
        data = db.execute_query(query)
        return data
    
    def dispatch_request(self) -> ResponseReturnValue:
        posts = self._get_blogs()
        return render_template('blog/index.html', posts=posts)
    
bp.add_url_rule('/index', view_func=BlogIndexView.as_view('index'))
    
class PostEditor:
    def _get_post_from_db(self, post_id: int, check_author: bool = True) -> Dict[str, Any]:
        query = f'SELECT * FROM posts WHERE id = {post_id};'
        global db
        data = db.execute_query(query)
        if len(data) == 0:
            abort(403, f'Post ID {post_id} does not exist')
        data = data[0]
        if check_author and data['author_id'] != g.user['id']:
            abort(403)
            
        return data
    
    def _write_to_posts_table(self, update: bool = False, **kwargs) -> None:
        global db
        if update:
            query = f'UPDATE posts SET title={kwargs["title"]}, body={kwargs["body"]} WHERE id = {kwargs["post_id"]};'
            db.execute_query(query)
        else:
            query = f'INSERT INTO posts (author_id, title, body) VALUES ({g.user["id"]}, "{kwargs["title"]}", "{kwargs["body"]}");'
            db.execute(query)
    
class AddPostView(views.View, PostEditor):
    methods = ('GET', 'POST')
    init_every_request = False
    decorators = (login_required,)
        
    def dispatch_request(self) -> ResponseReturnValue:
        error = None
        if request.method == 'POST':
            title = request.form['title']
            body = request.form['body']
            if g.user is None:
                error = 'You have to be logged in to post'
            elif title is None:
                error = 'Please give the post a title.'
            elif body is None or body.strip() == '':
                error = 'The post body cannot be empty.'
            else:
                self._write_to_posts_table(title=title, body=body)
                
        flash(error)
        return render_template('blog/post.html')
    
bp.add_url_rule('/add', view_func=AddPostView.as_view('add'))
    
class UpdatePostView(views.View, PostEditor):
    methods = ('GET', 'POST')
    init_every_request = False
    decorators = (login_required,)
    
    def dispatch_request(self, post_id: int) -> ResponseReturnValue:
        error = None
        post = self._get_post_from_db(post_id)
        if request.method == 'POST':
            if g.user['id'] != post['author_id']:
                error = 'You are not the owner of this post. Please log in as post owner.'
            else:
                title = request.form['title']
                body = request.form['body']
                self._write_to_posts_table(True, title=title, body=body)
        flash(error)
        return render_template('posts/updte.html', post=post)

bp.add_url_rule('/update/<int:post_id>', view_func=UpdatePostView.as_view('update'))                    
    
class DeletePostView(views.View):
    methods = ('GET',)
    init_every_request = False
    decorators = (login_required,)
    
    def _delete_post(self, post_id: int) -> None:
        query = f'DELETE FROM posts WHERE id={post_id};'
        db = get_db()
        db.execute_query(query)
    
    def dispatch_request(self, post_id: int) -> ResponseReturnValue:
        self._delete_post(post_id)
        return redirect(url_for('blog.index'))

bp.add_url_rule('/delete/<int:post_id>', view_func=AddPostView.as_view('delete'))

