from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
]

# ЭТОТ БЛОК ОБЯЗАТЕЛЕН, ИНАЧЕ ДЖАНГО НЕ ОТДАСТ ЛОКАЛЬНЫЕ КАРТИНКИ:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)