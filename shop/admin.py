from django.contrib import admin
from .models import Maker, Category, Product, Cart, CartItem, Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_price')
    list_filter = ('created_at',)
    
@admin.register(Maker)
class MakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'category', 'maker')
    list_filter = ('category', 'maker')
    search_fields = ('name', 'definition')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price')
    list_filter = ('cart',)