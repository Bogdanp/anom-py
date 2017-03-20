# anom + bottle guestbook example

This example demonstrates basic CRUD and query operations using anom
by building a simple guestbook web app.

## Setup

```
pip install -U -r requirements.txt
```

## Running

1. Run the Datastore emulator with `gcloud beta emulators datastore start`, then
1. in a separate terminal, run `$(gcloud beta emulators datastore env-init)` and
1. start the guestbook server with `python guestbook.py`

You should then be able to access it at http://localhost:8080.
