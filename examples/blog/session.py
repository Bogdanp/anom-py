from anom import Key, Model, props
from bottle import abort, request, redirect, response
from models import User
from uuid import uuid4


# [START session-model]
class Session(Model):
    user = props.Key(kind=User)

    @classmethod
    def create(cls, user):
        session = cls(user=user)
        session.key = Key(Session, str(uuid4()))
        return session.put()
# [END session-model]


# [START user-required]
def user_required(*permissions):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            session_id = request.get_cookie("sid")
            if not session_id:
                return redirect("/login")

            session = Session.get(session_id)
            if not session:
                return redirect("/login")

            user = session.user.get()
            if user is None:
                return redirect("/login")

            for permission in permissions:
                if permission not in user.permissions:
                    return abort(403)

            return fn(user, *args, **kwargs)
        return wrapper
    return decorator
# [END user-required]


# [START create-session]
def create_session(user):
    session = Session.create(user)
    response.set_cookie("sid", session.key.str_id)
# [END create-session]
