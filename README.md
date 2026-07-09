# frikr-django
Frikr (like Flickr for frikis). Another Django project

## Security notes

- The Django `SECRET_KEY` previously committed to this repository remains in the git history and must be considered compromised. Set a new secret via the `DJANGO_SECRET_KEY` environment variable (also `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS`) — never commit it.
- Django 1.11 is end-of-life and has known CVEs; upgrading to a supported Django LTS release is strongly recommended.
