from bottle import abort, get, post, redirect, request, run, view
from models import User, Post
from session import create_session, user_required


# [START index]
@get("/")
@view("index")
@user_required()
def index(user):
    cursor, tag = request.params.cursor, request.params.tag.strip()
    posts = Post.query().order_by(-Post.created_at)
    if tag:
        posts = posts.where(Post.tags == tag)

    pages = posts.paginate(page_size=2, cursor=cursor)
    return {"user": user, "pages": pages}
# [END index]


# [START post]
@get("/posts/<slug>")
@view("post")
@user_required("read")
def view_post(user, slug):
    post = Post.query().where(Post.slug == slug).get()
    if post is None:
        return abort(404)
    return {"post": post, "embedded": False}
# [END post]


# [START create]
@get("/new")
@view("create")
@user_required("create")
def create(user):
    return {}


@post("/new")
@view("create")
@user_required("create")
def do_create(user):
    title = request.forms.title
    tags = [tag.strip() for tag in request.forms.tags.split(",") if tag.strip()]
    body = request.forms.body
    post = Post(author=user, title=title, tags=tags, body=body).put()
    return redirect("/posts/" + post.slug)
# [END create]


# [START login]
@get("/login")
@view("login")
def login():
    return {}


@post("/login")
@view("login")
def do_login():
    username = request.forms.username
    password = request.forms.password
    user = User.login(username, password)
    if not user:
        return {"error": "Invalid credentials."}

    create_session(user)
    return redirect("/")
# [END login]


# [START run]
run(host="localhost", port=8080, debug=True, reloader=True)
# [END run]
