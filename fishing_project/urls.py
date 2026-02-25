from django.contrib import admin
from django.urls import path, include
from shop import urls as shop_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
]
