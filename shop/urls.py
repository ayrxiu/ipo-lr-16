from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views  # 👈 Добавили встроенные вьюхи Django
from . import views

# Инициализация роутера для API
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'makers', views.MakerViewSet, basename='maker')
router.register(r'carts', views.CartViewSet, basename='cart')
router.register(r'cartitems', views.CartItemViewSet, basename='cartitem')

urlpatterns = [
    # Основные страницы интерфейса
    path('', views.home, name='home'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Корзина и заказы
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Аутентификация и профиль
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.profile_page, name='profile_page'),
    
    # Встроенная авторизация Django (использует твои шаблоны в папочке registration)
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'), 
    
    # Перенаправление со старого URL на каталог
    path('products/', RedirectView.as_view(pattern_name='catalog', permanent=False)),    
    
    # Django Rest Framework API
    path('api/', include(router.urls)),
    path('api/me/', views.ProfileView.as_view(), name='api_profile'),
    path('api/orders/', views.OrderListView.as_view(), name='api_orders'),
]