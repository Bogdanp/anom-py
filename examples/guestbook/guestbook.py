# [START imports]
from anom import Model, props
from bottle import get, post, redirect, request, run, view
# [END imports]


# [START guestbook-entry-model]
class GuestbookEntry(Model):
    author = props.String(optional=True)
    message = props.Text()
    created_at = props.DateTime(indexed=True, auto_now_add=True)
# [END guestbook-entry-model]


# [START index-route]
@get("/")
@view("index")
def index():
    cursor = request.params.cursor
    pages = GuestbookEntry.query().order_by(-GuestbookEntry.created_at).paginate(page_size=1, cursor=cursor)
    return {"pages": pages}
# [END index-route]


# [START sign-route]
@post("/sign")
def sign():
    author = request.forms.author
    message = request.forms.message
    if not author or not message:
        return "<em>You must provide a message!</em>"

    GuestbookEntry(author=author, message=message).put()
    return redirect("/")
# [END sign-route]


# [START delete-route]
@post("/delete/<entry_id:int>")
def delete(entry_id):
    entry = GuestbookEntry.get(entry_id)
    if not entry:
        return "<h1>Entry not found.</h1>"

    entry.delete()
    return redirect("/")
# [END delete-route]


# [START run]
run(host="localhost", port=8080, debug=True, reloader=True)
# [END run]
