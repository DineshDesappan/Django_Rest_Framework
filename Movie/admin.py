from django.contrib import admin
# Register your models here

from . models import Movie, StreamPlatform, Review

admin.site.register(StreamPlatform)
admin.site.register(Movie)
admin.site.register(Review)
