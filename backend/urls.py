from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from api.views import frontend

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # Include URLs from our 'api' app
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('tinymce/', include('tinymce.urls')),
    re_path(r"^.*$", frontend),
]

# This is important for serving images you upload in the admin during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)