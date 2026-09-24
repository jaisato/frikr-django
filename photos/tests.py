# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase

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

		self.assertRedirects(self.client.get('/logout'), '/')
