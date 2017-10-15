# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from photos.models import Photo


class PhotoAdmin(admin.ModelAdmin):

	list_display = ('name', 'owner', 'owner_name', 'license', 'visibility')
	list_filter = ('license', 'visibility')
	search_fields = ('name', 'description')

	def owner_name(self, obj):
		return obj.owner.first_name + ' ' + obj.owner.last_name

	owner_name.short_description = 'Photo owner'
	owner_name.admin_order_field = 'owner'


admin.site.register(Photo, PhotoAdmin)
