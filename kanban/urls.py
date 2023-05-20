from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Kanban App"
admin.site.site_title = "Kanban Admin Panel"
admin.site.index_title = "Welcome to the Kanban Admin Panel"
