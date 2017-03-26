from anom import Model, props
from markdown import markdown
from passlib.context import CryptContext
from slugify import slugify


# [START password-property]
ctx = CryptContext(schemes=["sha256_crypt"])


class Password(props.String):
    def validate(self, value):
        return ctx.hash(super().validate(value))
# [END password-property]


# [START user-model]
class User(Model, poly=True):
    username = props.String(indexed=True)
    password = Password()
    created_at = props.DateTime(indexed=True, auto_now_add=True)
    updated_at = props.DateTime(indexed=True, auto_now=True)

    @classmethod
    def login(cls, username, password):
        user = User.query().where(User.username == username).get()
        if user is None:
            return None

        if not ctx.verify(password, user.password):
            return None

        if ctx.needs_update(user.password):
            user.password = password
            return user.put()

        return user

    @property
    def permissions(self):
        return ()
# [END user-model]


# [START editor-and-reader-models]
class Editor(User):
    @property
    def permissions(self):
        return ("create", "read", "edit", "delete")


class Reader(User):
    @property
    def permissions(self):
        return ("read",)
# [END editor-and-reader-models]


# [START post-model]
class Post(Model):
    author = props.Key(indexed=True, kind=User)
    title = props.String()

    def __compute_slug(self):
        if self.title is None:
            return None

        return slugify(self.title)

    def __compute_body(self):
        if self.body is None:
            return None

        return markdown(self.body)

    slug = props.Computed(__compute_slug)
    body = props.Text()
    body_markdown = props.Computed(__compute_body)
    tags = props.String(indexed=True, repeated=True)
    created_at = props.DateTime(indexed=True, auto_now_add=True)
    updated_at = props.DateTime(indexed=True, auto_now=True)
# [END post-model]


# [START init-database]
def init_database():
    users = list(User.query().run(keys_only=True))
    if users:
        return

    Editor(username="editor", password="editor").put()
    Reader(username="viewer", password="viewer").put()


init_database()
# [END init-database]
