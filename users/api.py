# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic import View
from rest_framework.renderers import JSONRenderer

from users.serializers import UserSerializer


class UserListAPI(View):
	"""
	API view of User list
	"""
	def get(self, request):
		"""
		Get all users
		:param request:
		:return:
		"""
		users = User.objects.all()
		serializer = UserSerializer(users, many=True)
		serialized_users = serializer.data
		renderer = JSONRenderer()
		json_users = renderer.render(serialized_users)

		return HttpResponse(json_users)
