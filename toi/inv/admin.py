from django.contrib import admin

from .models import Invitation, Photo, Rsvp

admin.site.register(Invitation)
admin.site.register(Photo)
admin.site.register(Rsvp)
