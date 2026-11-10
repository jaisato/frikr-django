# frikr-django
Frikr (like Flickr for frikis). Another Django project

## Security notes

This project runs on Python 3.10+ with Django 5.2 LTS (supported until April
2028) and Django REST framework 3.18. Keep both on their latest patch releases.

Two things need action from you regardless:

- `SECRET_KEY` used to be hard-coded in `frikr/settings.py` and is still in the
  git history. Generate a new one and pass it through `DJANGO_SECRET_KEY`.
  Sessions and password-reset links signed with the old key must be considered
  forgeable. With `DJANGO_DEBUG=false` the project refuses to start until
  `DJANGO_SECRET_KEY` is set, so the public development fallback cannot end up
  signing real sessions.
- `DEBUG` and `ALLOWED_HOSTS` now come from `DJANGO_DEBUG` and
  `DJANGO_ALLOWED_HOSTS`. Set `DJANGO_DEBUG=false` anywhere that is not a
  developer machine.

### Deployment settings (with `DJANGO_DEBUG=false`)

| Variable | Default | Effect |
| --- | --- | --- |
| `DJANGO_SECURE_COOKIES` | `true` | `Secure` flag on the session and CSRF cookies. Set `false` only for an http-only deployment. |
| `DJANGO_SECURE_SSL_REDIRECT` | `false` | Redirect every http request to https. |
| `DJANGO_SECURE_HSTS_SECONDS` | `0` | `Strict-Transport-Security` max-age. Read Django's docs before enabling. |
| `DJANGO_TRUST_X_FORWARDED_PROTO` | `false` | Trust `X-Forwarded-Proto: https` from a TLS-terminating proxy that overwrites that header. |
| `DJANGO_STATIC_ROOT` | `<repo>/staticfiles` | Target of `manage.py collectstatic`. |

## Checks

```sh
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

`.github/workflows/ci.yml` runs them on every pull request and push to
`master`, on Python 3.10 and 3.12, and then `manage.py check --deploy` with
`DJANGO_DEBUG=false`. `.github/dependabot.yml` proposes, once a week, the patch
releases of Django 5.2 and DRF and the updates of the pinned actions.
