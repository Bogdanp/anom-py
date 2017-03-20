from anom import Model, props
from bottle import get, post, redirect, request, run, template


class GuestbookEntry(Model):
    author = props.String(optional=True)
    message = props.Text()
    created_at = props.DateTime(indexed=True, auto_now_add=True)


@get("/")
def index():
    cursor = request.params.get("cursor")
    pages = GuestbookEntry.query().order_by(-GuestbookEntry.created_at).paginate(page_size=1, cursor=cursor)
    page = pages.fetch_next_page()
    return template("""
<h1>Guestbook</h1>

<h2>Sign guestbook</h2>
<form action="/sign" method="POST">
    <p><label>Name:<br/> <input name="name" /></label></p>
    <p><label>Message:<br/> <textarea name="message" rows="8" cols="80"></textarea></label></p>
    <button type="submit">Sign guestbook</button>
</form>

<hr/>

<h2>Entries:</h2>

% if not page:
    <small><em>There are currently no entries.</em></small>
% end

% for entry in page:
    <div>
        <p>{{entry.message}}</p>
        <h5>Signed by <strong>{{entry.author or 'anonymous'}}</strong> on <em>{{entry.created_at}}</em>.</h5>
        <form action="/delete/{{entry.key.int_id}}" method="POST">
            <button type="submit" onclick="return confirm('Are you sure?');">Delete</button>
        </form>
    </div>
% end

% if page:
    <br/><a href="/?cursor={{page.cursor}}">Next page</a>
% end
""", page=page)


@post("/sign", methods=("POST",))
def sign():
    author = request.forms.get("author")
    message = request.forms.get("message")
    if not message:
        return "<em>You must provide a message!</em>"

    entry = GuestbookEntry(author=author, message=message)
    entry.put()
    return redirect("/")


@post("/delete/<entry_id:int>", methods=("POST",))
def delete(entry_id):
    entry = GuestbookEntry.get(entry_id)
    if not entry:
        return "<h1>Entry not found.</h1>"

    entry.delete()
    return redirect("/")


run(host="localhost", port=8080, reload=True)
