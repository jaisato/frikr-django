# frikr-django
Frikr (like Flickr for frikis). Another Django project

## Security notes

This project runs on Python 3.10+ with Django 5.2 LTS (supported until April
2028) and Django REST framework 3.17. Keep both on their latest patch releases.

Two things need action from you regardless:

- `SECRET_KEY` used to be hard-coded in `frikr/settings.py` and is still in the
  git history. Generate a new one and pass it through `DJANGO_SECRET_KEY`.
  Sessions and password-reset links signed with the old key must be considered
  forgeable.
- `DEBUG` and `ALLOWED_HOSTS` now come from `DJANGO_DEBUG` and
  `DJANGO_ALLOWED_HOSTS`. Set `DJANGO_DEBUG=false` anywhere that is not a
  developer machine.
