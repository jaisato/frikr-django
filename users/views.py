# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import logout as dj_logout, authenticate, login as dj_login
from users.forms import LoginForm


def login(request):
	form = LoginForm()
	error_msg = []

	if request.method == 'POST':
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
					# if next doesn't exist, redirect to home
					return redirect(request.GET.get('next', 'photos_home'))
				else:
					error_msg.append('User is not active')

	context = {
		'errors': error_msg,
		'login_form': form
	}

	return render(request, 'users/login.html', context)


def logout(request):

	if request.user.is_authenticated():
		dj_logout(request)

	return redirect('photos_home')
