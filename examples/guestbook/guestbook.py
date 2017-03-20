from anom import Model, props
from bottle import SimpleTemplate, get, post, redirect, request, run


class GuestbookEntry(Model):
    author = props.String(optional=True)
    message = props.Text()
    created_at = props.DateTime(indexed=True, auto_now_add=True)


with open("templates/index.html") as f:
    _index_template = SimpleTemplate(f.read())


@get("/")
def index():
    cursor = request.params.get("cursor")
    pages = GuestbookEntry.query().order_by(-GuestbookEntry.created_at).paginate(page_size=1, cursor=cursor)
    page = pages.fetch_next_page()
    return _index_template.render(page=page)


@post("/sign", methods=("POST",))
def sign():
    author = request.forms.get("author")
    message = request.forms.get("message")
    if not message:
        return "<em>You must provide a message!</em>"

    GuestbookEntry(author=author, message=message).put()
    return redirect("/")


@post("/delete/<entry_id:int>", methods=("POST",))
def delete(entry_id):
    entry = GuestbookEntry.get(entry_id)
    if not entry:
        return "<h1>Entry not found.</h1>"

    entry.delete()
    return redirect("/")


run(host="localhost", port=8080, reload=True)
