# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase

from photos.models import Photo, PRIVATE, PUBLIC


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


class PhotoListApiOrderTest(TestCase):
	"""
	PhotoListAPI paginates, and pagination over an unordered queryset lets the
	database return rows in any order per query, so a photo could show up on
	two pages or on none.
	"""

	def test_pages_are_newest_first_and_do_not_overlap(self):
		owner = User.objects.create_user('bea', 'bea@example.com', 'S3gura-Clave-123')
		for i in range(12):
			Photo.objects.create(owner=owner, name='p%d' % i, url='http://example.com/%d.jpg' % i,
				license='CC', visibility=PUBLIC)

		first = self.client.get('/api/1.0/photos').json()['results']
		second = self.client.get('/api/1.0/photos?page=2').json()['results']
		ids = [p['id'] for p in first + second]

		self.assertEqual(len(ids), 12)
		self.assertEqual(ids, sorted(ids, reverse=True))


class PhotoListPagesTest(TestCase):
	"""
	/photos and /my-photos show one page of photos at a time, newest first.
	They used to render every photo in the table on every request.
	"""

	password = 'S3gura-Clave-123'

	def setUp(self):
		self.owner = User.objects.create_user('carla', 'carla@example.com', self.password)
		other = User.objects.create_user('dani', 'dani@example.com', self.password)
		for i in range(12):
			Photo.objects.create(owner=self.owner, name='pub%d' % i, url='http://example.com/%d.jpg' % i,
				license='CC', visibility=PUBLIC)
		Photo.objects.create(owner=other, name='private', url='http://example.com/x.jpg',
			license='CC', visibility=PRIVATE)

	@staticmethod
	def names(response):
		return [photo['name'] for photo in response.context['photos_list']]

	def test_the_public_listing_is_paginated_newest_first(self):
		first = self.client.get('/photos')
		second = self.client.get('/photos?page=2')

		self.assertEqual(self.names(first), ['pub%d' % i for i in range(11, 1, -1)])
		self.assertEqual(self.names(second), ['pub1', 'pub0'])
		self.assertContains(first, 'href="?page=2"')
		self.assertContains(second, 'href="?page=1"')

	def test_a_bad_page_number_falls_back_to_a_real_page(self):
		self.assertEqual(self.names(self.client.get('/photos?page=abc')), self.names(self.client.get('/photos')))
		for page in ('0', '99'):
			response = self.client.get('/photos?page=' + page)
			self.assertEqual(response.status_code, 200, page)
			self.assertEqual(self.names(response), ['pub1', 'pub0'], page)

	def test_the_pages_still_leave_out_other_peoples_private_photos(self):
		names = self.names(self.client.get('/photos')) + self.names(self.client.get('/photos?page=2'))
		self.assertEqual(len(names), 12)
		self.assertNotIn('private', names)

	def test_my_photos_is_paginated_newest_first_too(self):
		self.client.login(username='carla', password=self.password)
		first = self.client.get('/my-photos')
		second = self.client.get('/my-photos?page=2')

		self.assertEqual([p.name for p in first.context['user_photos']], ['pub%d' % i for i in range(11, 1, -1)])
		self.assertEqual([p.name for p in second.context['user_photos']], ['pub1', 'pub0'])
		self.assertContains(first, 'href="?page=2"')
