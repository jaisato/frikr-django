# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth import logout as djlogout


def login(request):

	return None


def logout(request):

	if request.user.is_authenticated():
		djlogout(request)

	return redirect('photos_home')
