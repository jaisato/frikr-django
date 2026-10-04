# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import warnings

from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import UnorderedObjectListWarning
from django.test import SimpleTestCase, TestCase

from photos.models import Photo, PUBLIC


class PagesAndApiRespondTest(TestCase):
	"""
	Smoke test for the upgrade to Django 5.2 / DRF 3.17: every page and API
	endpoint still resolves, renders and answers, for anonymous and logged-in
	users. It catches removed APIs (url(), is_safe_url(), staticfiles,
	is_authenticated()) at the point where they would break a request.
	"""

	password = 'S3gura-Clave-123'

	def setUp(self):
		self.user = User.objects.create_user('ana', 'ana@example.com', self.password)
		self.photo = Photo.objects.create(
			owner=self.user, name='p1', url='http://example.com/a.jpg', license='CC', visibility=PUBLIC)

	def test_anonymous_pages_and_api(self):
		for url in ['/', '/photos', '/photos/%d' % self.photo.pk, '/login',
				'/api/1.0/photos', '/api/1.0/photos/%d' % self.photo.pk]:
			self.assertEqual(self.client.get(url).status_code, 200, url)

	def test_logged_in_pages_api_and_logout(self):
		self.client.login(username='ana', password=self.password)
		for url in ['/my-photos', '/photos/new', '/api/1.0/users/%d' % self.user.pk]:
			self.assertEqual(self.client.get(url).status_code, 200, url)

		response = self.client.post('/api/1.0/photos', {'name': 'p2', 'url': 'http://example.com/b.jpg', 'license': 'CC'})
		self.assertEqual(response.status_code, 201)
		self.assertEqual(Photo.objects.get(name='p2').owner, self.user)

		# Logging out is POST-only (logout CSRF); a GET must not end the session.
		self.assertEqual(self.client.get('/logout').status_code, 405)
		self.assertEqual(self.client.get('/my-photos').status_code, 200)
		self.assertRedirects(self.client.post('/logout'), '/')
		self.assertEqual(self.client.get('/my-photos').status_code, 302)


class PhotoApiPaginationTest(TestCase):
	"""
	The photo list API paginates. An unordered queryset lets the database
	return rows in a different order per query, so pages could repeat or skip
	photos; Django flags it with UnorderedObjectListWarning.
	"""

	def test_pages_are_ordered_newest_first_and_do_not_overlap(self):
		user = User.objects.create_user('ana', 'ana@example.com', 'S3gura-Clave-123')
		for i in range(15):
			Photo.objects.create(owner=user, name='p%d' % i, url='http://example.com/%d.jpg' % i,
				license='CC', visibility=PUBLIC)

		with warnings.catch_warnings():
			warnings.simplefilter('error', UnorderedObjectListWarning)
			first = self.client.get('/api/1.0/photos').json()['results']
			second = self.client.get('/api/1.0/photos?page=2').json()['results']

		ids = [p['id'] for p in first + second]
		self.assertEqual(len(ids), 15)
		self.assertEqual(ids, sorted(ids, reverse=True))


class InsecureSecretKeyGuardTest(SimpleTestCase):
	"""
	The fallback SECRET_KEY is in the repository, so a deployment that forgot
	DJANGO_SECRET_KEY could have its sessions forged. With DEBUG off the
	settings must refuse to load rather than use it.
	"""

	def load_settings(self, **env):
		environ = {k: v for k, v in os.environ.items() if not k.startswith('DJANGO_')}
		environ.update(env, DJANGO_SETTINGS_MODULE='frikr.settings')
		return subprocess.run(
			[sys.executable, '-c', 'import django; django.setup()'],
			cwd=settings.BASE_DIR, env=environ, capture_output=True, text=True)

	def test_refuses_the_fallback_key_with_debug_off(self):
		result = self.load_settings(DJANGO_DEBUG='false')
		self.assertNotEqual(result.returncode, 0)
		self.assertIn('DJANGO_SECRET_KEY', result.stderr)

	def test_starts_with_debug_off_and_a_real_key(self):
		result = self.load_settings(DJANGO_DEBUG='false', DJANGO_SECRET_KEY='x' * 50)
		self.assertEqual(result.returncode, 0, result.stderr)

	def test_development_default_still_starts(self):
		result = self.load_settings()
		self.assertEqual(result.returncode, 0, result.stderr)
