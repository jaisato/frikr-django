# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import logout as dj_logout, authenticate, login as dj_login
from django.utils.http import url_has_allowed_host_and_scheme
from users.forms import LoginForm
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
					# Validate 'next' parameter to prevent open redirect attacks
					next_url = request.GET.get('next', '')
					if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
						return redirect(next_url)
					return redirect('photos_home')
				else:
					error_msg.append('User is not active')

		context = {
			'errors'    : error_msg,
			'login_form': form
		}

		return render(request, 'users/login.html', context)


class LogoutView(View):
	def get(self, request):

		if request.user.is_authenticated():
			dj_logout(request)

		return redirect('photos_home')
