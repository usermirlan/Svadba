from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import path

from inv import views

urlpatterns = [
    path("", lambda r: redirect("owner_list")),
    path("i/<slug:slug>/", views.invitation, name="invitation"),
    path("i/<slug:slug>/rsvp/", views.rsvp, name="rsvp"),
    path("i/<slug:slug>/guests/<str:token>/", views.guests, name="guests"),
    path("owner/login/", views.OwnerLogin.as_view(), name="owner_login"),
    path("owner/logout/", auth_views.LogoutView.as_view(next_page="owner_login"), name="owner_logout"),
    path("owner/", views.owner_list, name="owner_list"),
    path("owner/new/", views.owner_edit, name="owner_new"),
    path("owner/<int:pk>/", views.owner_edit, name="owner_edit"),
    path("owner/<int:pk>/delete/", views.owner_delete, name="owner_delete"),
    path("owner/photo/<int:pk>/delete/", views.owner_photo_delete, name="owner_photo_delete"),
    path("panel/", admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
