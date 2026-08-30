# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import logout as dj_logout, authenticate, login as dj_login
from users.forms import LoginForm
from django.utils.http import is_safe_url
from django.views.generic import View


class LoginView(View):
	def get(self, request):
		form = LoginForm()
		error_msg = []

		context = {
			'errors'    : error_msg,
			'login_form': form
		}

		return render(request, 'users/login.html', context)

	def post(self, request):
		error_msg = []
		form = LoginForm(request.POST)

		if form.is_valid():
			username = form.cleaned_data.get('usr')
			password = form.cleaned_data.get('pwd')
			user = authenticate(username=username, password=password)

			if user is None:
				error_msg.append('Invalid username or password')
			else:
				if user.is_active:
					dj_login(request, user)

					return redirect(self.get_redirect_url(request))
				else:
					error_msg.append('User is not active')

		context = {
			'errors'    : error_msg,
			'login_form': form
		}

		return render(request, 'users/login.html', context)

	@staticmethod
	def get_redirect_url(request):
		"""
		Where to send the user once they are logged in.

		`?next=` was passed straight to redirect(), so anyone could hand out
		https://this-site/login/?next=https://evil.example/, and a victim who
		logged in - seeing a genuine login page on the real domain, which is
		the whole point of the trick - landed on the attacker's page already
		trusting it. The usual follow-up is a lookalike asking them to sign in
		"again".

		is_safe_url() is what Django's own LoginView uses for this: it rejects
		absolute URLs pointing anywhere but this host, and require_https stops
		an https session being bounced down to http.

		Falls back to the 'photos_home' view name, which is what redirect()
		received before whenever `next` was absent.
		"""
		next_url = request.GET.get('next')

		if next_url and is_safe_url(
			url=next_url,
			allowed_hosts={request.get_host()},
			require_https=request.is_secure(),
		):
			return next_url

		return 'photos_home'


class LogoutView(View):
	def get(self, request):

		if request.user.is_authenticated():
			dj_logout(request)

		return redirect('photos_home')
