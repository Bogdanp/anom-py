# anom + bottle blog example

This example demonstrates simple blog functionality built using anom
and bottle.

## Setup

```
pip install -U -r requirements.txt
```

## Running

1. Run the Datastore emulator with `gcloud beta emulators datastore start`, then
1. in a separate terminal, run `$(gcloud beta emulators datastore env-init)` and
1. start the blog server with `python blog.py`

You should then be able to access it at http://localhost:8080.
