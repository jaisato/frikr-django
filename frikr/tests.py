# -*- coding: utf-8 -*-
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

LOAD_SETTINGS = 'import frikr.settings as s; print(s.SECRET_KEY)'


class SecretKeyFallbackTestCase(SimpleTestCase):
	"""
	The fallback SECRET_KEY is public, so it may only be used while DEBUG is
	on. settings.py runs at import, so each case imports it in a fresh process
	with its own environment.
	"""

	def load_settings(self, **env):
		environment = {
			key: value for key, value in os.environ.items()
			if key not in ('DJANGO_SECRET_KEY', 'DJANGO_DEBUG')
		}
		environment.update(env)

		return subprocess.run(
			[sys.executable, '-c', LOAD_SETTINGS],
			cwd=settings.BASE_DIR, env=environment, capture_output=True, text=True,
		)

	def test_refuses_the_fallback_key_with_debug_off(self):
		for key in (None, ''):
			env = {'DJANGO_DEBUG': 'false'}
			if key is not None:
				env['DJANGO_SECRET_KEY'] = key

			result = self.load_settings(**env)

			self.assertNotEqual(result.returncode, 0)
			self.assertIn('ImproperlyConfigured', result.stderr)

	def test_accepts_a_real_key_with_debug_off(self):
		result = self.load_settings(DJANGO_DEBUG='false', DJANGO_SECRET_KEY='a-real-key-from-the-environment')

		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(result.stdout.strip(), 'a-real-key-from-the-environment')

	def test_keeps_the_fallback_for_local_development(self):
		result = self.load_settings()

		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(result.stdout.strip(), 'insecure-development-key-change-me')


class DeploymentHardeningTestCase(SimpleTestCase):
	"""
	With DEBUG off the session and CSRF cookies must carry the Secure flag
	unless the deployment explicitly says it serves plain http.
	"""

	PRINT_FLAGS = (
		'import frikr.settings as s; '
		'print(getattr(s, "SESSION_COOKIE_SECURE", False), getattr(s, "CSRF_COOKIE_SECURE", False), '
		'getattr(s, "SECURE_PROXY_SSL_HEADER", None) is not None)'
	)

	def flags(self, **env):
		environment = {
			key: value for key, value in os.environ.items()
			if not key.startswith('DJANGO_')
		}
		environment.update(env)
		result = subprocess.run(
			[sys.executable, '-c', self.PRINT_FLAGS],
			cwd=settings.BASE_DIR, env=environment, capture_output=True, text=True,
		)
		self.assertEqual(result.returncode, 0, result.stderr)
		return result.stdout.split()

	def test_secure_cookies_by_default_with_debug_off(self):
		flags = self.flags(DJANGO_DEBUG='false', DJANGO_SECRET_KEY='a-real-key')

		self.assertEqual(flags, ['True', 'True', 'False'])

	def test_secure_cookies_can_be_switched_off_explicitly(self):
		flags = self.flags(DJANGO_DEBUG='false', DJANGO_SECRET_KEY='a-real-key', DJANGO_SECURE_COOKIES='false')

		self.assertEqual(flags[:2], ['False', 'False'])

	def test_trusts_x_forwarded_proto_only_when_asked(self):
		flags = self.flags(DJANGO_DEBUG='false', DJANGO_SECRET_KEY='a-real-key', DJANGO_TRUST_X_FORWARDED_PROTO='true')

		self.assertEqual(flags[2], 'True')

	def test_local_development_keeps_plain_cookies(self):
		flags = self.flags()

		self.assertEqual(flags[:2], ['False', 'False'])
