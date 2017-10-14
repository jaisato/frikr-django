# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import logout as dj_logout, authenticate, login as dj_login


def login(request):
	error_msg = []
	if request.method == 'POST':
		username = request.POST.get('usr')
		password = request.POST.get('pwd')
		user = authenticate(username=username, password=password)

		if user is None:
			error_msg.append('Invalid username or password')
		else:
			if user.is_active:
				dj_login(request, user)
				return redirect('photos_home')
			else:
				error_msg.append('User is not active')

	context = {
		'errors': error_msg
	}

	return render(request, 'users/login.html', context)


def logout(request):

	if request.user.is_authenticated():
		dj_logout(request)

	return redirect('photos_home')
