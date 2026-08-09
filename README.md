# frikr-django
Frikr (like Flickr for frikis). Another Django project

## Security notes

This project targets Python 2.7 / Django 1.11, both of which are end-of-life and
no longer receive security fixes. Treat anything deployed from it as
unsupported, and plan a port to Python 3 with a maintained Django release.

Two things need action from you regardless:

- `SECRET_KEY` used to be hard-coded in `frikr/settings.py` and is still in the
  git history. Generate a new one and pass it through `DJANGO_SECRET_KEY`.
  Sessions and password-reset links signed with the old key must be considered
  forgeable.
- `DEBUG` and `ALLOWED_HOSTS` now come from `DJANGO_DEBUG` and
  `DJANGO_ALLOWED_HOSTS`. Set `DJANGO_DEBUG=false` anywhere that is not a
  developer machine.
